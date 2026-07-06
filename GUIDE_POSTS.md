# Guide Posts

This page explains how PointsBot handles `[Guide]` posts and how those posts can earn points for their authors.

## What is a Guide Post?

A guide post is any submission whose title contains the text `[Guide]` (case-insensitive).

Example:

- `How to fix the build error [Guide]`
- `[Guide] Setting up the project environment`

## How a Guide Award is Triggered

PointsBot awards a point to the author of the guide when the original poster acknowledges the guide in a top-level comment.

To trigger the award:

- the submission title must contain `[Guide]`
- the acknowledgment comment must be a root-level reply on that submission
- if the commenter is not a moderator, the acknowledgment comment must contain one of the following commands:
  - `!Solved`
  - `!solved`
  - `!Helped`
  - `!helped`
- if the commenter is a moderator, the acknowledgment comment must contain one of the following commands:
  - `/Solved`
  - `/solved`
  - `/Helped`
  - `/helped`
- the commenter must not be the same user as the guide author

The bot detects the acknowledgment using the same solved-pattern logic as regular solved posts, but it only applies when the submission is a guide post.

## What the Bot Does

When a valid guide acknowledgment is found, PointsBot:

- records the guide award in the database
- increments the guide author’s point total by 1
- replies to the OP’s acknowledgment comment with a progress/update message
- updates the guide author’s flair when they reach a new level, unless they are a moderator

The bot will not award the same guide more than once for a given trigger author and submission.

## Important Notes

- Guide awards are only detected for top-level OP comments. Replies to other comments do not count.
- The bot does not allow a user to award points to themselves via guide acknowledgments.
- Duplicate acknowledgments from the same commenter on the same guide do not award additional points, unless the commenter is a moderator.
- Moderators can award multiple guide points to the same guide author by posting multiple top-level `/helped` or `/solved` acknowledgments on the same submission.
- Guide awards are identified by `[Guide]` in the submission title, regardless of any configured `valid_tags`.

## Configuration

In `pointsbot.toml`, the guide feature relies on the standard title rule and does not require extra configuration.

The `valid_tags` setting only applies to the normal solved-post workflow, not the guide acknowledgment workflow.

Example config:

```toml
[core]
subreddit = "your_subreddit_name"
valid_tags = "tutorial,help,wiki"  # optional - regular solved posts must match one of these tags
```

## Example Flow

1. `u/GuideAuthor` posts a guide titled: `How to configure the bot [Guide]`
2. `u/OP` reads the guide and posts a top-level reply on the submission:
   - `!Solved`
3. PointsBot detects the guide acknowledgment and awards 1 point to `u/GuideAuthor`.
4. PointsBot replies to `u/OP` confirming the guide was acknowledged.

## Bot Reply

The bot replies to the acknowledgment comment with a header like:

> Thanks! This [Guide] post was acknowledged.

Then it includes the normal progress and footer links configured in `pointsbot.toml`.
