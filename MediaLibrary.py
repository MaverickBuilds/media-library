# We import OS to access our file system in Windows
# os.listdir()      → returns a list of strings (filenames/folder names only — no path attached)
# os.path.join()    → returns a string (combines path segments with correct slashes)
# os.path.isdir()   → returns a boolean (True = folder, False = file)
# os.path.dirname() → returns a string (removes the last segment from a path)
# os.path.basename()→ returns a string (only the last segment of a path — opposite of dirname)
# os.path.normpath()→ returns a string (standardises all slashes to \ on Windows)
# os.path.exists()  → returns a boolean (True if the path exists, False if not)
import os
# Subprocess is imported to allow us to excecute our media player application and pass a path to it of our media file selected
# subprocess.Popen() → launches a program without waiting — Python keeps running immediately
# subprocess.run()  → launches a program and WAITS for it to close before continuing
import subprocess
# Flask is huge so we import Flask and render_template as that is all we need
# Flask             → the web framework class
# render_template() → takes a filename string + keyword arguments, returns HTML to the browser
#                     keyword argument left side = name the template knows it by
#                     keyword argument right side = the Python variable containing the data
# redirect()        → takes a URL string, sends the browser to that URL
from flask import Flask, render_template, redirect
# sqlite3 is imported as we use this database to remember what we have watched and resume episodes from where we left off
# sqlite3.connect()   → returns a connection object (the open link to the .db file)
# connection.cursor() → returns a cursor object (used to send SQL commands)
# cursor.execute()    → sends a SQL command — returns nothing useful on its own
# cursor.fetchall()   → returns a list of tuples — each tuple is one row from the database
#                       e.g. [("path/to/ep.mkv", 1, 90000.0)]  or  [] if no rows match
import sqlite3
# requests.get()    → returns a Response object — .text is a string of the full page content
import requests
# re.search()       → returns a Match object or None — .group(1) extracts the captured text as a string
# re.sub()          → returns a string — replaces all pattern matches with the replacement text
import re
# time.sleep()      → pauses Python for the given number of seconds
import time


# We are defining our APP to call it later and run it
app = Flask(__name__)

# base_path is being defined as our main file path to look for shows
base_path = (r"C:\Users\maver\Videos\Anime")


# We are defining a function called folder_browse with the parameter path
def folder_browse(path):
    # Series is set to the list of items within the parameter we pass to the function
    series = os.listdir(path)
    # An empty list is created only with "Go back" as to go back later on
    video_list = ["Go back"]
    # A for loop starts going through the files within the series variable
    for file in series:
        # Seeing whether it is a video file or another folder
        if file.endswith((".mp4", ".mkv", ".avi")) or os.path.isdir(os.path.join(path, file)):
            # If either criteria is met it is added to the list Video_list
            video_list.append(file)
    # Print both an index and the itmes added to that list to go further
    for index, file in enumerate(video_list):
        print(index, file)

    while True:
        try:
            # 1. Valid number: it breaks and  it returns the full path of the selection by combining the parameter path, and the selected item within video_list
            select = int(input("Select your watch : "))
            if select >= 1 and select <= len(video_list):
                break
            # 2. 0 as Input: It goes back by removing the last /(and text} from the path
            elif select == 0:
                return os.path.dirname(path)
            # 3. Out of Range: It asks for a number between 0 and the length of items in the video_list by hitting the else.
            else:
                print("Please select a number between 0 and " + str(len(video_list)))
        # 4. Invalid Input: prints please select a corresponding number when the except is hit
        except:
            print ("Please select the corresponding number for your show: ")
    return os.path.join(path, video_list[select])


# connection is a connection object — the open link to MediaLibrary.db (created if it doesn't exist)
# cursor is a cursor object — the tool we use to send SQL commands to that connection
# CREATE TABLE IF NOT EXISTS — runs once at startup, skipped silently if the table already exists
# Shows table columns: episode_path (TEXT → string), watched (INTEGER → int), timestamp (REAL → float)
connection = sqlite3.connect("MediaLibrary.db")
cursor = connection.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS Shows(
               episode_path TEXT,
               watched INTEGER,
               timestamp REAL) """)

# 1. Defines the route for our main home page
@app.route('/')
def home():
    # 2. options is set to the list of items within base_path
    options = os.listdir(base_path)
    # 3. An empty dictionary is created
    image_dict = {}
    # 4. Loop through each show in options
    for show in options:
        # 5. image_path is a file system path - used by Python to check if the image exists
        image_path = os.path.join ("static", "images", show + ".jpg") 
        # 6. If the image exists, store the URL path for HTML to use
        if os.path.exists(image_path):
            image_dict[show] = ("/static/images/" + show + ".jpg")
        # 7. Otherwise point to the placeholder image URL path
        else:
            image_dict[show] = ("/static/images/placeholder.jpg")


    # 8. Return home.html and pass options and image_dict for the template to use               
    return render_template("home.html", options=options, image_dict=image_dict)


# 1. Defines the browse route - captures any depth of URL path
# folder_path is a string — Flask captures everything after /browse/ in the URL
# e.g. URL /browse/Sword Art Online/Season 1  →  folder_path = "Sword Art Online/Season 1"
# folder_path uses forward slashes (URL format) — used for links and redirects
@app.route('/browse/<path:folder_path>')
def browse(folder_path):
    #2. show_path combines base_path and folder_path to get the full file system path
    # show_path is a string — the full Windows path with consistent backslashes after normpath
    # e.g. "C:\Users\maver\Videos\Anime\Sword Art Online\Season 1"
    # Rule: folder_path → URLs and Flask routes | show_path → os functions and file system
    show_path = os.path.normpath(os.path.join(base_path, folder_path))
    #3. If show_path is a directory, list its contents
    # current_folder is a string — the cleaned folder name for the <h1> heading
    # os.path.basename() returns only the last segment e.g. "Season 1 [1080p]"
    # re.sub() strips bracket content, .strip() removes leftover whitespace
    current_folder = re.sub(r'\(.*?\)|\[.*?\]', "", os.path.basename(folder_path)).strip()
    # os.path.isdir() returns a boolean — True if show_path is a folder, False if it's a file
    # True → list contents and render browse page | False → launch MPC-HC
    if os.path.isdir(show_path):
        # contents is a list of strings — each string is a filename or folder name (no path attached)
        # e.g. ["Season 1", "Season 2"]  or  ["ep01.mkv", "ep02.mkv"]
        contents = os.listdir(show_path)
        #4. An empty list for filtered video files and folders
        # video_list starts as an empty list — will hold filtered strings (names only, no path)
        video_list = []
        # New connection per request — required because Flask runs each request in a separate thread
        # SQLite connections can only be used by the thread that created them
        connection = sqlite3.connect("MediaLibrary.db")
        cursor = connection.cursor()
        # watched_dict: keys = strings (filenames), values = booleans (True/False watched status)
        # timestamp_dict: keys = strings (filenames), values = strings (formatted HH:MM:SS) or 0
        # display_dict: keys = strings (filenames), values = strings (cleaned display names)
        watched_dict = {}
        timestamp_dict = {}
        display_dict = {}
        #5. Back_path removes the last section from the URL for go back navigation
        # back_path is a string — the URL path one level up e.g. "Sword Art Online/Season 1" → "Sword Art Online"
        # Empty string "" if already at top level — Jinja2 treats "" as falsy so {% if back_path %} handles both cases
        back_path = os.path.dirname(folder_path)
        #6. Loop through contents - if it's a video file or folder, add to video_list
        # On each iteration, file is a string (one name from contents)
        # .endswith() returns a boolean — True if the name ends with a video extension
        for file in contents:
            if file.endswith((".mp4", ".mkv", ".avi")) or os.path.isdir(os.path.join(show_path, file)):
                video_list.append(file)
        # Second loop — builds watched_dict, timestamp_dict, display_dict for each item in video_list
        for file in video_list:
            # cursor.execute() sends a parameterised SELECT — ? is replaced by the tuple value
            # the tuple value is the full normalised path — must match the format stored during INSERT
            # fetchall() returns a list of tuples e.g. [("path", 1, 90000.0)]  or  [] if no match
            cursor.execute("""SELECT * FROM Shows WHERE episode_path = ?""",(os.path.join(show_path, file),))
            watched = cursor.fetchall()
            # watched is truthy if it has data (episode in DB), falsy if empty list (not watched yet)
            if watched:
                watched_dict[file] = True                                              # boolean
                display_dict[file] = re.sub(r'\(.*?\)|\[.*?\]', "", file)             # string — cleaned name
                # watched[0] → first tuple in the list | watched[0][2] → third element (timestamp float)
                # // integer division discards decimal | % modulo returns the remainder
                # f-string :02d formats as 2-digit zero-padded integer e.g. 5 → "05"
                timestamp_dict[file] = watched[0][2]
                total_seconds = (timestamp_dict[file] // 1000)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                timestamp_dict[file] = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"  # string
            else:
                watched_dict[file] = False                                             # boolean
                timestamp_dict[file] = 0                                               # integer
                display_dict[file] = re.sub(r'\(.*?\)|\[.*?\]', "", file)             # string — cleaned name

        #7. Return browse.html and pass folder_path, video_list and back_path to the template
        # render_template() passes each keyword argument to the template as a variable
        # left side of = → the name the template accesses it by (e.g. {{ watched_dict[seasons] }})
        # right side of = → the Python variable containing the actual data
        return render_template("browse.html", current_folder=current_folder, folder_path=folder_path, contents=video_list, back_path=back_path, watched_dict=watched_dict, timestamp_dict=timestamp_dict, display_dict=display_dict)
    else:
        # Create a new DB connection and cursor for this request (threading — each request needs its own)
        connection = sqlite3.connect("MediaLibrary.db")
        cursor = connection.cursor()
        # Search the DB for this episode using normpath so slashes match
        cursor.execute("""SELECT * FROM Shows WHERE episode_path = ?""",(os.path.normpath(show_path),))
        # haveThis is a list of tuples — e.g. [("C:\path\ep.mkv", 1, 90000.0)]  or  [] if no match
        haveThis = cursor.fetchall()
        # If the episode isn't in the DB, insert it as watched with 0 timestamp
        # if not haveThis: empty list is falsy → episode not in DB → INSERT as new
        # saved_time = 0 (integer) — no position to resume from
        if not haveThis:
            cursor.execute("""INSERT INTO Shows VALUES (?, ?, ?)""", (os.path.normpath(show_path), 1, 0))
            saved_time = 0
        else:
            # If it already exists, update watched status and grab the saved timestamp from the DB
            # haveThis[0] → the first (and only) tuple | haveThis[0][2] → third element (timestamp float)
            cursor.execute("""UPDATE Shows SET watched = ? WHERE episode_path = ?""",(1, os.path.normpath(show_path),))
            saved_time = haveThis[0][2]
        # Save the changes to the DB
        connection.commit()

        # Convert saved timestamp from milliseconds to hours, minutes, seconds
        # saved_time is a float (DB REAL column) — // integer division discards the decimal
        # total_seconds // 3600 → whole hours | (total_seconds % 3600) // 60 → remaining minutes
        # total_seconds % 60 → remaining seconds after minutes are removed
        # int() converts float to integer before :02d formatting (requires integer)
        # :02d → 2-digit zero-padded integer e.g. 5 → "05", 12 → "12"
        total_seconds = (saved_time // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        # If there's a saved position, launch MPC-HC and resume from that timestamp
        # subprocess.Popen() returns a Popen object (not stored) — launches MPC-HC without waiting
        if saved_time > 0:
            subprocess.Popen([r"C:\Program Files\MPC-HC\mpc-hc64.exe", show_path, "/fullscreen", "/startpos", f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"])
        # Otherwise launch MPC-HC from the beginning
        else:
            subprocess.Popen([r"C:\Program Files\MPC-HC\mpc-hc64.exe","/fullscreen", show_path,])

            
        # Wait 2 seconds for MPC-HC to open before polling starts
        time.sleep(2)
        # Get the initial state of MPC-HC from its web interface
        response1 = requests.get("http://127.0.0.1:13579/variables.html")
        state = re.search(r'<p id="statestring">(.+)</p>', response1.text)

        # While MPC-HC is playing or paused, keep polling every 2 seconds for the current position
        # state.group(1) is a string e.g. "Playing", "Paused", "Stopped"
        # or operator: must use explicit == on both sides — state == "Playing" or state == "Paused"
        #   (state == "Playing" or "Paused" is WRONG — "Paused" alone is always truthy)
        while state.group(1) == "Playing" or state.group(1) == "Paused":
            try:
                # requests.get() returns a Response object — .text is a string of the full HTML page
                # re.search() returns a Match object — .group(1) extracts the captured text as a string
                # state.group(1) → string e.g. "Playing" | timestamp.group(1) → string e.g. "90000"
                response = requests.get("http://127.0.0.1:13579/variables.html")
                state = re.search(r'<p id="statestring">(.+)</p>', response.text)
                timestamp = re.search(r'<p id="position">(.+)</p>', response.text)
                print(timestamp.group(1))
                print(state.group(1))
                time.sleep(2)
            # When MPC-HC closes, requests.get() raises a ConnectionError — caught here
            # timestamp.group(1) is a string (ms as text) — saved to DB, break exits the loop
            except:
                print(timestamp.group(1))
                cursor.execute("""UPDATE Shows SET timestamp = ? WHERE episode_path = ?""",(timestamp.group(1), os.path.normpath(show_path),))
                connection.commit()
                break
        
        # episodes_folder is a string — the folder containing the current episode
        # os.path.dirname() removes the filename from show_path, leaving the parent folder path
        episodes_folder = os.path.dirname(show_path)
        # contents is a list of strings — same pattern as the folder branch above
        contents = os.listdir(episodes_folder)
        episodes_list = []
        # duration.group(1) is a string (total duration in ms from MPC-HC)
        duration = re.search(r'<p id="duration">(.+)</p>', response.text)

        # int() converts the ms strings to integers for comparison
        # -5000 gives a 5-second buffer — catches episodes that end slightly before the true duration
        if int(timestamp.group(1)) >= int(duration.group(1))-5000:
            # Same filtering pattern as browse folder branch — builds list of episode strings
            for file in contents:
                if file.endswith((".mp4", ".mkv", ".avi")) or os.path.isdir(os.path.join(episodes_folder, file)):
                    episodes_list.append(file)

            # selected_episode is a string — just the filename e.g. "ep01.mkv"
            # .index() returns an integer — the position of selected_episode in episodes_list
            selected_episode = os.path.basename(show_path)
            current = episodes_list.index(selected_episode)
            # If not on the last episode, build the redirect URL string and send browser to countdown
            # episodes_list[current+1] is a string — the next episode's filename
            if current < len(episodes_list) -1:
                return redirect("/countdown/" + os.path.dirname(folder_path) + "/" + episodes_list[current+1])
            else:
                return redirect("/browse/" + os.path.dirname(folder_path))
        else:
            return redirect("/browse/" + os.path.dirname(folder_path))

@app.route('/countdown/<path:next_episode>')
def countdown(next_episode):
    episode_path = os.path.dirname(next_episode)
    episode_name = os.path.basename(next_episode)
    display_name = re.sub(r'\(.*?\)|\[.*?\]', "", episode_name)
    # next_episode is a string — the URL path of the next episode
    # e.g. "Sword Art Online/Season 1/ep02.mkv"
    # captured by Flask from /countdown/<path:next_episode> — same mechanism as folder_path in browse()
    # render_template passes it to countdown.html as a template variable named next_episode
    return render_template("countdown.html", next_episode=next_episode, episode_path=episode_path, display_name=display_name)

# Starts the Flask app 
app.run(debug=True)