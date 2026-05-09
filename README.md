# PointsBot

## Overview
PointsBot is a Reddit bot that monitors posts in a subreddit, awards points to users who solve problems, and updates their flair to reflect their achievement levels. When the original poster marks a comment as solved (e.g., by replying "!Solved"), the bot awards a point to the solver, tracks their progress, and notifies them with a reply comment. Points accumulate to unlock new levels, and progress is visually represented with stars and progress bars.

## Features
- Monitors subreddit posts for solutions
- Awards points to users whose comments are marked as solved
- Updates user flair based on their point level
- Notifies users of their progress and next level
- Prevents awarding points to moderators
- Consolidates points into stars for easier progress tracking

## Installation (Docker Compose)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### (Easy) Use a prebuilt image

1. Create a docker-compose.yml file in your chosen directoy, with the following contents:

```yaml
   services:
     pointsbot:
       image: ghcr.io/imonlytryingtohelp/pointsbot:latest
       container_name: pointsbot
       volumes:
         - ./data:/root/.pointsbot
       restart: unless-stopped
   ```

2. Configure the bot:
   - Pre-create the config file using the sample config.

3. Start the bot:
   ```bash
   docker-compose up -d
   ```

### (Advanced) Build your own image

1. Clone this repository:
   ```bash
   git clone https://github.com/Imonlytryingtohelp/PointsBot.git
   cd PointsBot
   ```
2. Create a `docker-compose.yml` file in the project root with the following content:
   ```yaml
   services:
     pointsbot:
       build: .
       container_name: pointsbot
       volumes:
         - ./data:/root/.pointsbot
       restart: unless-stopped
   ```
3. Configure the bot:
   - Pre-create the config file using the sample config.

4. Build and start the bot:
   ```bash
   docker-compose up --build -d
   ```

## Usage
- The bot will run in the background and monitor your subreddit.
- Configuration and logs are stored in the `.pointsbot` directory.
- To stop the bot:
  ```bash
  docker-compose down
  ```

## License
MIT License. See LICENSE.md for details.

## Credits
Original author: Collin U. Rapp (u/GlipGlorp7)
