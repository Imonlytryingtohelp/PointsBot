import logging
import re
import sys
import time
from collections import namedtuple
from logging.handlers import RotatingFileHandler

import praw
import prawcore

from . import config, database, level, reply
from .update_checker import start_update_checker
from . import __version__ as __version__

### Globals ###

USER_AGENT = 'PointsBot (by u/Imonlytryingtohelp_)'

# The pattern that determines whether a post is marked as solved
SOLVED_PATTERN = re.compile('!([Hh]elped|[Ss]olved)')
MOD_SOLVED_PATTERN = re.compile('/([Hh]elped|[Ss]olved)')
MOD_REMOVE_PATTERN = re.compile('/[Rr]emove[Pp]oint')
RATE_LIMIT_DEFAULT_DELAY = 60


def is_rate_limit_error(exc):
    if isinstance(exc, prawcore.exceptions.TooManyRequests):
        return True
    if isinstance(exc, praw.exceptions.APIException):
        return getattr(exc, 'error_type', None) == 'RATELIMIT' or 'ratelimit' in str(exc).lower()
    return False


def get_rate_limit_delay(exc):
    if isinstance(exc, prawcore.exceptions.TooManyRequests):
        response = getattr(exc, 'response', None)
        headers = getattr(response, 'headers', {}) or {}
        retry_after = headers.get('x-ratelimit-reset') or headers.get('retry-after')
        if retry_after is not None:
            try:
                reset_time = int(retry_after)
            except (TypeError, ValueError):
                return RATE_LIMIT_DEFAULT_DELAY
            current_time = int(time.time())
            if reset_time > current_time:
                return max(1, reset_time - current_time)
        return RATE_LIMIT_DEFAULT_DELAY

    if isinstance(exc, praw.exceptions.APIException):
        message = str(exc).lower()
        match = re.search(r'(\d+)\s+seconds?', message)
        if match:
            return max(1, int(match.group(1)))
    return RATE_LIMIT_DEFAULT_DELAY


def execute_with_rate_limit_retry(operation, operation_name, retries=3):
    last_error = None
    for attempt in range(retries):
        try:
            return operation()
        except Exception as exc:
            if not is_rate_limit_error(exc):
                raise
            last_error = exc
            if attempt == retries - 1:
                break
            delay = get_rate_limit_delay(exc)
            logging.warning('Reddit rate limited while %s; waiting %s seconds before retrying', operation_name, delay)
            time.sleep(delay)
    if last_error is not None:
        raise last_error
    return None


### Main Function ###


def run():
    print_welcome_message()

    cfg = config.load()

    file_handler = RotatingFileHandler(cfg.log_path, maxBytes=1024*1024, backupCount=3, encoding='utf-8')
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)

    logging.basicConfig(handlers=[file_handler, console_handler],
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s:%(module)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    levels = cfg.levels
    db = database.Database(cfg.database_path)

    # Run indefinitely, reconnecting any time a connection is lost
    while True:
        try:
            reddit = praw.Reddit(client_id=cfg.client_id,
                                 client_secret=cfg.client_secret,
                                 username=cfg.username,
                                 password=cfg.password,
                                 user_agent=USER_AGENT)
            logging.info('Connected to Reddit as %s', reddit.user.me())
            access_type = 'read-only' if reddit.read_only else 'write'
            logging.info(f'Has {access_type} access to Reddit')

            subreddit = reddit.subreddit(cfg.subreddit)
            logging.info('Watching subreddit %s', subreddit.title)
            is_mod = subreddit.moderator(redditor=reddit.user.me())
            logging.info(f'Is {"" if is_mod else "NOT "}moderator for subreddit')

            # Start the update checker in background so mods are notified of new releases
            try:
                start_update_checker(reddit, cfg.subreddit, 'PointsBot', __version__)
            except Exception:
                logging.debug('Failed to start update checker', exc_info=True)

            monitor_comments(reddit, subreddit, db, levels, cfg)

        # Ignoring other potential exceptions for now, since we may not be able
        # to recover from them as well as from these ones
        except prawcore.exceptions.TooManyRequests as e:
            delay = get_rate_limit_delay(e)
            logging.warning('Reddit rate limited while connecting; sleeping %s seconds before retrying', delay)
            time.sleep(delay)
        except prawcore.exceptions.RequestException as e:
            logging.error('Unable to connect to Reddit')
            logging.error('Error message: %s', e)
            logging.error('Trying again')
        except prawcore.exceptions.ServerError as e:
            logging.error('Lost connection to Reddit')
            logging.error('Error message: %s', e)
            logging.error('Attempting to reconnect')


def monitor_comments(reddit, subreddit, db, levels, cfg):
    """Monitor new comments in the subreddit, looking for confirmed solutions."""
    while True:
        try:
            for comm in subreddit.stream.comments(skip_existing=True, pause_after=0):
                if comm is None:
                    continue
                if comm.author == reddit.user.me():
                    logging.info('Comment was posted by this bot')
                    continue
                if comm.author.name == reddit.user.me().name:
                    logging.info('Comment was posted by this bot name')
                    continue

                logging.info('Found comment')
                logging.debug('Comment author: "%s"', comm.author.name)
                logging.debug('Comment text: "%s"', comm.body)

                if is_guide_award_comment(comm):
                    guide_author = comm.submission.author
                    if guide_author is None:
                        logging.warning('Guide submission author unknown; skipping guide award')
                        continue
                    if guide_author.name == comm.author.name:
                        logging.info('Guide comment author is also submission author; skipping guide award')
                        continue
                    if db.has_guide_award_for_submission(comm.submission, comm.author):
                        logging.info('Guide award already recorded for user "%s" on this submission', comm.author.name)
                        continue

                    logging.info('Guide top-level acknowledgment found; awarding point to guide author "%s"', guide_author.name)
                    rowcount = db.add_guide_award_for_submission(comm.submission, guide_author, comm.author, comm)
                    if rowcount == 0:
                        logging.info('Guide award was not added, likely duplicate')
                        continue

                    points = db.get_points(guide_author)
                    logging.info('Total points for guide author "%s": %d', guide_author.name, points)
                    if points > 0:
                        level_info = level.user_level_info(points, levels)
                    else:
                        level_info = None

                    reply_body = reply.make(guide_author,
                                            points,
                                            level_info,
                                            feedback_url=cfg.feedback_url,
                                            scoreboard_url=cfg.scoreboard_url,
                                            is_add=True,
                                            header=reply.guide_header())
                    try:
                        execute_with_rate_limit_retry(lambda: comm.reply(reply_body), 'replying to guide acknowledgment comment')
                        logging.info('Replied to the guide acknowledgment comment')
                        logging.debug('Reply body: %s', reply_body)
                    except praw.exceptions.APIException as e:
                        logging.error('Unable to reply to guide acknowledgment comment: %s', e)
                        # Do not remove the awarded point in this case; the award was still recorded.

                    if level_info and level_info.current and level_info.current.points == points:
                        lvl = level_info.current
                        logging.info('Guide author reached level: %s', lvl.name)
                        is_mod = execute_with_rate_limit_retry(
                            lambda: subreddit.moderator(redditor=guide_author),
                            'checking guide author moderator status')
                        if not is_mod:
                            logging.info('Guide author is not mod; setting flair')
                            logging.info('Flair text: %s', lvl.name)
                            logging.info('Flair template ID: %s', lvl.flair_template_id)
                            execute_with_rate_limit_retry(
                                lambda: subreddit.flair.set(guide_author,
                                                            text=lvl.name,
                                                            flair_template_id=lvl.flair_template_id),
                                'setting flair for guide author')
                        else:
                            logging.info('Guide author is mod; don\'t alter flair')
                    continue

                mark_as_solved, remove_point, is_mod_command = marks_as_solved(comm)
                if mark_as_solved:
                    logging.info('Comment marks issue as solved')
                elif remove_point:
                    logging.info('Comment removes point')
                else:
                    # Skip this "!solved" comment
                    logging.info('Comment does not have a valid command')
                    continue

                if is_mod_command:
                    logging.info('Comment was submitted by mod')
                elif is_valid_tag(comm, cfg.tags):
                    logging.info('Comment has a valid tag')

                solver, solution_comment = find_solver_and_comment(comm)
                solver_has_already_solved = db.has_already_solved_once(solution_comment.submission, solver)
                if not remove_point and solver_has_already_solved:
                    logging.info('User "%s" has already solved this submission once', solver.name)
                    logging.info('No additional points awarded')
                    continue

                if remove_point:
                    db.soft_remove_point_for_solution(comm.submission, solver, comm.author, comm)
                    logging.info('Removed point for user "%s"', solver.name)
                else:
                    logging.info('Submission solved')
                    logging.debug('Solution comment:')
                    logging.debug('Author: %s', solution_comment.author.name)
                    logging.debug('Body:   %s', solution_comment.body)
                    db.add_point_for_solution(comm.submission, solver, solution_comment, comm.author, comm)
                    logging.info('Added point for user "%s"', solver.name)

                points = db.get_points(solver)
                logging.info('Total points for user "%s": %d', solver.name, points)
                if points > 0:
                    level_info = level.user_level_info(points, levels)
                else:
                    level_info = None

                # Reply to the comment marking the submission as solved
                reply_body = reply.make(solver,
                                        points,
                                        level_info,
                                        feedback_url=cfg.feedback_url,
                                        scoreboard_url=cfg.scoreboard_url,
                                        is_add=not remove_point)
                try:
                    execute_with_rate_limit_retry(lambda: comm.reply(reply_body), 'replying to solved comment')
                    logging.info('Replied to the comment')
                    logging.debug('Reply body: %s', reply_body)
                except praw.exceptions.APIException as e:
                    logging.error('Unable to reply to comment: %s', e)
                    if remove_point:
                        db.add_back_point_for_solution(comm.submission, solver)
                        logging.error('Re-added point that was just removed from user "%s"', solver.name)
                    else:
                        db.remove_point_and_delete_solution(comm.submission, solver)
                        logging.error('Removed point that was just awarded to user "%s"', solver.name)
                    logging.error('Skipping comment')
                    continue

                # Check if (non-mod) user flair should be updated to new level
                if level_info and level_info.current and level_info.current.points == points:
                    lvl = level_info.current
                    logging.info('User reached level: %s', lvl.name)
                    is_mod = execute_with_rate_limit_retry(
                        lambda: subreddit.moderator(redditor=solver),
                        'checking solver moderator status')
                    if not is_mod:
                        logging.info('User is not mod; setting flair')
                        logging.info('Flair text: %s', lvl.name)
                        logging.info('Flair template ID: %s', lvl.flair_template_id)
                        execute_with_rate_limit_retry(
                            lambda: subreddit.flair.set(solver,
                                                        text=lvl.name,
                                                        flair_template_id=lvl.flair_template_id),
                            'setting flair for solver')
                    else:
                        logging.info('Solver is mod; don\'t alter flair')
        except Exception as e:
            if not is_rate_limit_error(e):
                raise
            delay = get_rate_limit_delay(e)
            logging.warning('Reddit rate limited while streaming comments; sleeping %s seconds before retrying', delay)
            time.sleep(delay)
            continue


### Reddit Comment Functions ###

SolutionResponseRule = namedtuple('SolutionResponseRule',
                                  'description success_msg failure_msg check')

OP_RESPONSE_RULES = [
    SolutionResponseRule(
        'user "solved" pattern',
        'Comment contains user "solved" pattern',
        'Comment does not contain user "solved" pattern',
        lambda c: SOLVED_PATTERN.search(c.body),
    ),
    SolutionResponseRule(
        'is a reply (not top-level)',
        'Comment is a reply to another comment',
        'Comment is a top-level comment',
        lambda c: not c.is_root,
    ),
    SolutionResponseRule(
        'author is OP',
        'Comment author is submission OP',
        'Comment author is not submission OP',
        lambda c: c.is_submitter,
    ),
    SolutionResponseRule(
        "OP can't solve own problem",
        'Submission OP is different from solution author',
        'Submission OP is marking own comment as solution',
        lambda c: not c.is_root and not c.parent().is_submitter,
    ),
]

MOD_RESPONSE_RULES = [
    SolutionResponseRule(
        'contains mod "solved" pattern',
        'Comment contains mod "solved" pattern',
        'Comment does not contain mod "solved" pattern',
        lambda c: MOD_SOLVED_PATTERN.search(c.body),
    ),
    SolutionResponseRule(
        'is a reply (not top-level)',
        'Comment is a reply to another comment',
        'Comment is a top-level comment',
        lambda c: not c.is_root,
    ),
    SolutionResponseRule(
        'author is mod',
        'Comment author is a mod',
        'Comment author is not a mod',
        # TODO Initialize rules in a function so that they can include other functions
        lambda c: is_mod_comment(c),
    ),
]

MOD_REMOVE_RULES = [
    SolutionResponseRule(
        'contains mod "removepoint" pattern',
        'Comment contains mod "removepoint" pattern',
        'Comment does not contain mod "removepoint" pattern',
        lambda c: MOD_REMOVE_PATTERN.search(c.body),
    ),
    SolutionResponseRule(
        'is a reply (not top-level)',
        'Comment is a reply to another comment',
        'Comment is a top-level comment',
        lambda c: not c.is_root,
    ),
    SolutionResponseRule(
        'author is mod',
        'Comment author is a mod',
        'Comment author is not a mod',
        lambda c: is_mod_comment(c),
    ),
]

# GENERAL_RESPONSE_RULES = []


def check_rules(rules, comment):
    all_rules_passed = True
    for rule in rules:
        rule_passed = rule.check(comment)
        logging.info(rule.success_msg if rule_passed else rule.failure_msg)
        all_rules_passed = all_rules_passed and rule_passed
    return all_rules_passed


def marks_as_solved(comment):
    """Return True if the comment meets the criteria for marking the submission
    as solved, False otherwise.
    """
    # TODO should enforce that only one or the other can pass?
    op_rules_pass = check_rules(OP_RESPONSE_RULES, comment)
    if op_rules_pass:
        logging.info('OP marking submission as solved')

    mod_rules_pass = check_rules(MOD_RESPONSE_RULES, comment)
    if mod_rules_pass:
        logging.info('Mod marking submission as solved')

    mod_remove_pass = check_rules(MOD_REMOVE_RULES, comment)
    if mod_remove_pass:
        logging.info('Mod removing point')

    return op_rules_pass or mod_rules_pass, mod_remove_pass, mod_rules_pass or mod_remove_pass


def is_mod_comment(comment):
    return comment.subreddit.moderator(redditor=comment.author)


def is_guide_post(submission):
    title = submission.title
    return title is not None and '[guide]' in title.lower()


def is_guide_award_comment(comment):
    if comment is None or comment.author is None or comment.submission is None:
        return False
    if not comment.is_root:
        return False
    if not SOLVED_PATTERN.search(comment.body):
        return False
    if not is_guide_post(comment.submission):
        return False
    if comment.submission.author is None:
        return False
    if comment.submission.author.name == comment.author.name:
        return False
    return True


def is_valid_tag(solved_comment, valid_tags):
    """Return True if this comments post has one of the allowed tags, False otherwise.
    If there aren't any tags configured, skip this check"""
    if valid_tags is None:
        return True

    submission_title = solved_comment.submission.title.lower()

    for valid_tag in valid_tags:
        if f"[{valid_tag}]" in submission_title:
            return True

    return False


def find_solver_and_comment(solved_comment):
    """Determine the redditor responsible for solving the question."""
    # TODO plz make this better someday
    # return solved_comment.parent().author
    solution_comment = solved_comment.parent()
    return solution_comment.author, solution_comment


### Print & Logging Functions ###


def print_welcome_message():
    print_separator_line()
    print('\n*** Welcome to PointsBot! ***\n')
    print_separator_line()
    print('\nThis bot will monitor the subreddit specified in the '
          'configuration file as long as this program is running.')
    print('\nOriginally created by GlipGlorp7, reworked and maintained by Imonlytryingtohelp_')
    print('\nAny Reddit activity that occurs while this program is not running '
          'will be missed.')
    print('\nThe output from this program can be referenced if any issues are '
          'to occur, and the relevant error message or crash report can be '
          'sent to the developer by reporting an issue on the Github page.')
    print('\nGithub - https://github.com/Imonlytryingtohelp/PointsBot\n')
    print_separator_line()


def print_separator_line():
    print('#' * 80)

