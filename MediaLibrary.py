import os
import subprocess
from flask import Flask, render_template, redirect
import sqlite3
import requests
import re
import time


app = Flask(__name__)

base_path = (r"C:\Users\maver\Videos\Anime")


def folder_browse(path):
    series = os.listdir(path)
    video_list = ["Go back"]
    for file in series:
        if file.endswith((".mp4", ".mkv", ".avi")) or os.path.isdir(os.path.join(path, file)):
            video_list.append(file)
    for index, file in enumerate(video_list):
        print(index, file)

    while True:
        try:
            select = int(input("Select your watch : "))
            if select >= 1 and select <= len(video_list):
                break
            elif select == 0:
                return os.path.dirname(path)
            else:
                print("Please select a number between 0 and " + str(len(video_list)))
        except:
            print("Please select the corresponding number for your show: ")
    return os.path.join(path, video_list[select])


connection = sqlite3.connect("MediaLibrary.db")
cursor = connection.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS Shows(
               episode_path TEXT,
               watched INTEGER,
               timestamp REAL) """)


@app.route('/')
def home():
    options = os.listdir(base_path)
    image_dict = {}
    for show in options:
        image_path = os.path.join("static", "images", show + ".jpg")
        if os.path.exists(image_path):
            image_dict[show] = ("/static/images/" + show + ".jpg")
        else:
            image_dict[show] = ("/static/images/placeholder.jpg")
    return render_template("home.html", options=options, image_dict=image_dict)


@app.route('/browse/<path:folder_path>')
def browse(folder_path):
    # folder_path = URL path (forward slashes) | show_path = full Windows path (backslashes)
    show_path = os.path.normpath(os.path.join(base_path, folder_path))
    current_folder = re.sub(r'\(.*?\)|\[.*?\]', "", os.path.basename(folder_path)).strip()
    if os.path.isdir(show_path):
        contents = os.listdir(show_path)
        video_list = []
        # New connection per request — SQLite connections can't be shared across Flask threads
        connection = sqlite3.connect("MediaLibrary.db")
        cursor = connection.cursor()
        watched_dict = {}
        timestamp_dict = {}
        display_dict = {}
        back_path = os.path.dirname(folder_path)
        for file in contents:
            if file.endswith((".mp4", ".mkv", ".avi")) or os.path.isdir(os.path.join(show_path, file)):
                video_list.append(file)
        for file in video_list:
            cursor.execute("""SELECT * FROM Shows WHERE episode_path = ?""", (os.path.join(show_path, file),))
            watched = cursor.fetchall()
            if watched:
                watched_dict[file] = True
                display_dict[file] = re.sub(r'\(.*?\)|\[.*?\]', "", file)
                timestamp_dict[file] = watched[0][2]
                total_seconds = (timestamp_dict[file] // 1000)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                timestamp_dict[file] = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            else:
                watched_dict[file] = False
                timestamp_dict[file] = 0
                display_dict[file] = re.sub(r'\(.*?\)|\[.*?\]', "", file)

        return render_template("browse.html", current_folder=current_folder, folder_path=folder_path, contents=video_list, back_path=back_path, watched_dict=watched_dict, timestamp_dict=timestamp_dict, display_dict=display_dict)
    else:
        # New connection per request — SQLite connections can't be shared across Flask threads
        connection = sqlite3.connect("MediaLibrary.db")
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM Shows WHERE episode_path = ?""", (os.path.normpath(show_path),))
        haveThis = cursor.fetchall()
        if not haveThis:
            cursor.execute("""INSERT INTO Shows VALUES (?, ?, ?)""", (os.path.normpath(show_path), 1, 0))
            saved_time = 0
        else:
            cursor.execute("""UPDATE Shows SET watched = ? WHERE episode_path = ?""", (1, os.path.normpath(show_path),))
            saved_time = haveThis[0][2]
        connection.commit()

        # Convert ms timestamp to HH:MM:SS for MPC-HC /startpos flag
        total_seconds = (saved_time // 1000)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if saved_time > 0:
            subprocess.Popen([r"C:\Program Files\MPC-HC\mpc-hc64.exe", show_path, "/fullscreen", "/startpos", f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"])
        else:
            subprocess.Popen([r"C:\Program Files\MPC-HC\mpc-hc64.exe", "/fullscreen", show_path])

        time.sleep(2)
        response1 = requests.get("http://127.0.0.1:13579/variables.html")
        state = re.search(r'<p id="statestring">(.+)</p>', response1.text)

        # or requires explicit == on both sides — "Paused" alone is always truthy
        while state.group(1) == "Playing" or state.group(1) == "Paused":
            try:
                response = requests.get("http://127.0.0.1:13579/variables.html")
                state = re.search(r'<p id="statestring">(.+)</p>', response.text)
                timestamp = re.search(r'<p id="position">(.+)</p>', response.text)
                print(timestamp.group(1))
                print(state.group(1))
                time.sleep(2)
            except:
                # MPC-HC closed — ConnectionError raised, save final position and exit loop
                print(timestamp.group(1))
                cursor.execute("""UPDATE Shows SET timestamp = ? WHERE episode_path = ?""", (timestamp.group(1), os.path.normpath(show_path),))
                connection.commit()
                break

        episodes_folder = os.path.dirname(show_path)
        contents = os.listdir(episodes_folder)
        episodes_list = []
        duration = re.search(r'<p id="duration">(.+)</p>', response.text)

        # -5000ms buffer catches episodes that end just before the true duration
        if int(timestamp.group(1)) >= int(duration.group(1)) - 5000:
            for file in contents:
                if file.endswith((".mp4", ".mkv", ".avi")) or os.path.isdir(os.path.join(episodes_folder, file)):
                    episodes_list.append(file)
            selected_episode = os.path.basename(show_path)
            current = episodes_list.index(selected_episode)
            if current < len(episodes_list) - 1:
                return redirect("/countdown/" + os.path.dirname(folder_path) + "/" + episodes_list[current + 1])
            else:
                return redirect("/browse/" + os.path.dirname(folder_path))
        else:
            return redirect("/browse/" + os.path.dirname(folder_path))


@app.route('/countdown/<path:next_episode>')
def countdown(next_episode):
    episode_path = os.path.dirname(next_episode)
    episode_name = os.path.basename(next_episode)
    display_name = re.sub(r'\(.*?\)|\[.*?\]', "", episode_name)
    return render_template("countdown.html", next_episode=next_episode, episode_path=episode_path, display_name=display_name)


app.run(debug=True)
