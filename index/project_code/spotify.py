import os
import re
import hashlib
import time
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from yt_dlp import YoutubeDL
import pygame
import threading

# === SETTINGS ===
SPOTIFY_CLIENT_ID = "05a2b6bdbd6340959f69a4073a4b4f86"
SPOTIFY_CLIENT_SECRET = "5f649f2805884a329ad197520250f29c"
SPOTIFY_REDIRECT_URI = "http://localhost:8000/callback"
PLAYLIST_ID = '1FdixOmnorQbFb4cNchYBg'
DOWNLOAD_DIR = 'index/static/music'

# === INIT SPOTIPY ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope='playlist-read-private playlist-modify-public playlist-modify-private'
))

# === SPOTIFY TRACKS ===
def get_playlist_tracks(sp, playlist_id):
    tracks = []
    results = sp.playlist_items(playlist_id)
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return [{
        'name': item['track']['name'],
        'artists': ', '.join([artist['name'] for artist in item['track']['artists']]),
        'id': item['track']['id']
    } for item in tracks]

def get_playlist_hash(tracks):
    track_str = ''.join([f"{t['name']} - {t['artists']}" for t in tracks])
    return hashlib.md5(track_str.encode()).hexdigest()

# === FILENAME TOOLS ===
def sanitize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', '', text)

# === YT DOWNLOAD ===
def download_song(song_name, artist):
    target_filename = sanitize_filename(f"{song_name} - {artist}.mp3").lower()
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.lower() == target_filename:
            print(f"✅ Already downloaded: {filename}")
            return

    print(f"🔍 Downloading: {song_name} by {artist}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, f"{sanitize_filename(song_name)} - {sanitize_filename(artist)}.%(ext)s"),
        'quiet': True,
        'noplaylist': True,
        'cachedir': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([f"ytsearch1:{song_name} {artist}"])
        except Exception as e:
            print(f"❌ Failed to download {song_name} - {artist}: {e}")

# === CLEANUP ===
def cleanup_extra_downloads(playlist_tracks):
    expected_filenames = {
        sanitize_filename(f"{track['name']} - {track['artists']}.mp3").lower()
        for track in playlist_tracks
    }
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith('.mp3') and filename.lower() not in expected_filenames:
            path = os.path.join(DOWNLOAD_DIR, filename)
            os.remove(path)
            print(f"🗑️ Removed outdated song: {filename}")

# === GLOBAL STATE ===
current_index = 0
playlist = []
playlist_tracks = []

# === MUSIC PLAYER ===
def play_next():
    global current_index, playlist, playlist_tracks
    if current_index < len(playlist):
        song_path = playlist[current_index]
        print(f"🎧 Now playing: {song_path.name}")
        pygame.mixer.music.load(str(song_path))
        pygame.mixer.music.play()
    else:
        print("🎉 Playlist finished.")

# === MANUAL UPDATE FUNCTION ===
def manual_update():
    global playlist, playlist_tracks, current_index

    print("🔄 Starting manual playlist sync...")
    playlist_tracks = get_playlist_tracks(sp, PLAYLIST_ID)

    for track in playlist_tracks:
        download_song(track['name'], track['artists'])
        time.sleep(1)

    cleanup_extra_downloads(playlist_tracks)
    playlist = sorted(Path(DOWNLOAD_DIR).glob("*.mp3"))
    current_index = 0
    play_next()

# === SKIP FUNCTION ===
def skip_song():
    global current_index, playlist, playlist_tracks
    if current_index < len(playlist):
        song_path = playlist[current_index]
        print(f"⏩ Skipping and removing: {song_path.name}")
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

        song_name = sanitize_filename(song_path.stem)
        for track in playlist_tracks:
            if song_name.lower() == sanitize_filename(f"{track['name']} - {track['artists']}").lower():
                sp.playlist_remove_all_occurrences_of_items(PLAYLIST_ID, [track['id']])
                print(f"❌ Removed {track['name']} by {track['artists']} from Spotify.")
                break

        os.remove(song_path)
        current_index += 1
        play_next()
    else:
        print("⚠️ No more songs to skip.")

# === COMMAND LISTENER ===
def command_listener():
    while True:
        command = input("").strip().lower()
        if command == "!update":
            manual_update()
        elif command == "!skip":
            skip_song()

# === MAIN ===
if __name__ == '__main__':
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_volume(0.1)

    print("💻 Type `!update` to sync the playlist.")
    print("💻 Type `!skip` to skip the current song.")

    threading.Thread(target=command_listener, daemon=True).start()
    manual_update()

    # Auto-play next song when one finishes
    while True:
        if not pygame.mixer.music.get_busy() and current_index < len(playlist):
            current_index += 1
            play_next()
        time.sleep(1)
