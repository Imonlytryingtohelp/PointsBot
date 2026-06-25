# Running PointsBot with Docker Compose

## Quick Start

1. **Copy the example config:**
   ```bash
   cp pointsbot.toml.example pointsbot_data/pointsbot.toml
   ```

2. **Edit the config file with your Reddit bot credentials and settings:**
   ```bash
   nano pointsbot_data/pointsbot.toml
   ```
   
   Required fields:
   - `subreddit` - the subreddit to monitor
   - `client_id` - your Reddit OAuth client ID
   - `client_secret` - your Reddit OAuth client secret
   - `username` - your bot's Reddit username
   - `password` - your bot's Reddit password

3. **Start the bot:**
   ```bash
   docker-compose up
   ```

4. **Stop the bot:**
   ```bash
   docker-compose down
   ```

## Configuration Details

All configuration is stored in `pointsbot_data/pointsbot.toml`. The directory structure will be created automatically:

```
pointsbot_data/
├── pointsbot.toml    # Configuration file
├── pointsbot.db      # Database (auto-created)
└── pointsbot.log     # Log file (auto-created)
```

## Running in Detached Mode

To run the bot in the background:

```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

## Stopping the Bot

```bash
docker-compose down
```

## Getting Reddit OAuth Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Create a new application (select "script")
3. Copy the client ID and client secret from the app details
4. Use your bot's Reddit account username and password

For more information, see the [Reddit OAuth documentation](https://github.com/reddit-archive/reddit/wiki/OAuth2).
