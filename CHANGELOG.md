# Changelog

All notable changes to this project are documented in this file.

The changelog only lists notable changes for each version, since 1.6.0.

## [1.6.0]
- Added: Guide award support — award points when a top-level OP comment
  acknowledges a guide post (detected and handled by the bot, with database
  tracking to prevent duplicates).
- Added: Respect configured valid tags for solved posts so only tagged posts
  are eligible when tags are set.
- Fixed: More robust reply handling — failures to reply no longer remove awarded
  points, and transient API errors are handled gracefully.
- Fixed: Robust rate limit handling - bot no longer restarts when encountering rate-limiting.   
- Updated docker image to python 3.10
- Updated PRAW to 8.0.2  
- Added update chekcer to notify mods (via modmail) when a new version is available. 


