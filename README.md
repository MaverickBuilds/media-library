# MediaLibrary
A personal media browser and watch tracker built with Flask and Python.

Browse your local anime/video library through a web interface, launch episodes directly in MPC-HC, and automatically resume from where you left off. The app polls MPC-HC's built-in web interface while an episode is playing to track your position in real time, saving it to a local SQLite database when you close the player.

## Features
- Browse your local video library through a clean web interface with cover art
- Launch episodes directly in MPC-HC (fullscreen, with resume support)
- Tracks watched status and playback position per episode via SQLite
- Resumes from your saved timestamp when you reopen an episode
- Auto-advances to the next episode with a countdown page when an episode finishes
- Cleans up display names by stripping bracket/parenthesis tags (e.g. [1080p], (BluRay))
- Placeholder cover art for shows without a matching image

## How It Works
1. The home page lists all shows found in your configured video folder
2. Clicking a show browses into its folder — seasons, then episodes
3. Selecting an episode launches MPC-HC and begins polling its web interface every 2 seconds
4. When the player closes, the last known timestamp is saved to the database
5. If the episode played to within 5 seconds of the end, a countdown page appears and auto-plays the next episode

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite (via sqlite3)
- **Player Integration:** MPC-HC Web Interface (HTTP polling)
- **Frontend:** HTML, Jinja2 templates
- **Other:** os, subprocess, requests, re, time
