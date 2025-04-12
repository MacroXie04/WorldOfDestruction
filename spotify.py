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
DOWNLOAD_DIR = 'index\static\music'

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

# === MUSIC PLAYER ===
def play_songs_in_order(folder, playlist_tracks):
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_volume(0.7)

    playlist = sorted(Path(folder).glob("*.mp3"))
    if not playlist:
        print("⚠️ No songs found to play.")
        return

    current_index = 0
    playing = True
    current_song_path = None  # To store the current song's path

    while playing and current_index < len(playlist):
        song_path = playlist[current_index]
        print(f"🎧 Now playing: {song_path.name}")
        pygame.mixer.music.load(str(song_path))
        pygame.mixer.music.play()

        current_song_path = song_path  # Store current song path for skipping

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Remove the song from the folder after it finishes playing
        os.remove(song_path)
        print(f"🗑️ Removed {song_path.name} from the downloads folder.")

        # Remove the song from the Spotify playlist
        song_name = sanitize_filename(song_path.stem)
        for track in playlist_tracks:
            if song_name.lower() == sanitize_filename(f"{track['name']} - {track['artists']}").lower():
                sp.playlist_remove_all_occurrences_of_items(PLAYLIST_ID, [track['id']])
                print(f"❌ Removed {track['name']} by {track['artists']} from the Spotify playlist.")
                break

        current_index += 1
        if current_index >= len(playlist):
            print("🎉 Playlist finished.")
            playing = False

    print("Playback finished.")
    return current_song_path  # Return the current song path for skipping

# === MANUAL UPDATE FUNCTION ===
def manual_update():
    print("🔄 Starting manual playlist sync...")

    playlist_tracks = get_playlist_tracks(sp, PLAYLIST_ID)
    current_hash = get_playlist_hash(playlist_tracks)
    print("📦 Syncing new playlist...")

    for track in playlist_tracks:
        download_song(track['name'], track['artists'])
        time.sleep(1)

    cleanup_extra_downloads(playlist_tracks)
    play_songs_in_order(DOWNLOAD_DIR, playlist_tracks)

# === SKIP FUNCTION (Updated) ===
def skip_song(playlist_tracks, current_song_path):
    pygame.mixer.music.stop()
    print("⏩ Song skipped.")

    # Remove the song from the downloads folder and Spotify playlist
    song_name = sanitize_filename(current_song_path.stem)
    for track in playlist_tracks:
        if song_name.lower() == sanitize_filename(f"{track['name']} - {track['artists']}").lower():
            sp.playlist_remove_all_occurrences_of_items(PLAYLIST_ID, [track['id']])
            print(f"❌ Removed {track['name']} by {track['artists']} from the Spotify playlist.")
            break

    # Remove the song from the downloads folder
    os.remove(current_song_path)
    print(f"🗑️ Removed {current_song_path.name} from the downloads folder.")

    # Move to the next song
    return play_songs_in_order(DOWNLOAD_DIR, playlist_tracks)  # Play the next song

# === ASYNC FUNCTION TO ALLOW UPDATES AND SKIP WHILE PLAYING ===
def update_and_skip_async():
    current_song_path = None  # Store current song path to skip
    playlist_tracks = get_playlist_tracks(sp, PLAYLIST_ID)

    while True:
        command = input("Enter command: ")
        if command.strip() == "!update":
            manual_update()
        elif command.strip() == "!skip":
            if current_song_path:
                current_song_path = skip_song(playlist_tracks, current_song_path)
            else:
                print("⚠️ No song is currently playing to skip.")

# === MAIN ===
if __name__ == '__main__':
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print("💻 Type `!update` to manually update the playlist and play music.")
    print("💻 Type `!skip` to skip the current song.")

    # Start the update and skip listener in a separate thread
    threading.Thread(target=update_and_skip_async, daemon=True).start()

    # Initial playlist download and playback
    playlist_tracks = get_playlist_tracks(sp, PLAYLIST_ID)
    current_song_path = play_songs_in_order(DOWNLOAD_DIR, playlist_tracks)
