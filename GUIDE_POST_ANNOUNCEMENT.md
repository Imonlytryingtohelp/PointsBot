# New Feature: [Guide] Post Acknowledgments

We’ve added a new PointsBot feature to reward authors who write helpful guide posts.

## What this does

If a submission is marked as a guide by including `[Guide]` in the title, and the original poster acknowledges that guide in a top-level comment, PointsBot will award one point to the guide author.

This is intended to encourage high-quality guide posts and make it easier for helpful authors to earn recognition.

## How to use it

1. Create your post with `[Guide]` in the title.
2. Follow the subreddit’s normal title/tag rules as usual.
3. When the guide helped OP, the original poster should reply with a top-level comment containing one of these commands:
   - `!Solved`
   - `!solved`
   - `!Helped`
   - `!helped`

   Moderators may instead award guide points using top-level moderator commands:
   - `/Solved`
   - `/solved`
   - `/Helped`
   - `/helped`

Example:

- `[Guide] [Java] How to fix the launcher crash`
- OP replies: `!Solved`

## What counts

- The guide post must have `[Guide]` in the title.
- The acknowledgment must be a top-level comment under the submission.
- The comment must be a top-level reply under the submission.
- If the comment is from the original poster (OP), it must contain one of the supported OP commands listed above.
- If the comment is from a moderator, it must contain one of the supported moderator commands listed above.
- The guide author and the commenter must be different users.

## What the bot does

When a valid guide acknowledgment is found, PointsBot will:

- record the guide award in the database
- grant the guide author 1 point
- reply to the acknowledgment comment with an update message
- update the guide author’s flair if they reach a new level and are not a moderator

## Important notes

- Replies to other comments do not count. Only top-level OP comments trigger the award.
- OP cannot award a point to themselves.
- The same OP cannot award the same guide post more than once.
- `[Guide]` is a special marker for PointsBot, but you should still follow the sub’s normal title and tag rules.

## Why this matters

This feature is designed to reward authors who make useful guide posts, while keeping the sub’s normal tagging and posting rules intact. It helps the community recognize quality help and gives guide authors a chance to earn points for their effort.

If you have questions about how to use `[Guide]` posts or what title format works best, feel free to ask in the comments!