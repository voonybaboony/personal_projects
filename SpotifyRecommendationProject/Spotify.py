import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from textblob import TextBlob
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from flask import Flask, request, render_template
import time

os.environ['SPOTIPY_CLIENT_ID'] = "16cf4d44b6114d8bbf8dafbc7fdbfbea"
os.environ['SPOTIPY_CLIENT_SECRET'] = "94e46316d38948c1b78bc45270608728"
os.environ['SPOTIPY_REDIRECT_URI'] = "http://localhost:8080/callback"

app = Flask(__name__)

scope = "user-library-read"
sp_oauth = spotipy.oauth2.SpotifyOAuth(scope=scope,
                                       client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                       client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                       redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
sp = spotipy.Spotify(auth_manager=sp_oauth)


def get_artist_uri(artist_name):
    results = sp.search(q=artist_name, type='artist')

    # Extract the artist URI from the search results
    artist_uri = results['artists']['items'][0]['uri']
    return artist_uri


def get_song_uri(song_name):
    results = sp.search(q=song_name, type='track')

    song_uri = results['tracks']['items'][0]['uri']
    return song_uri


def get_playlist_uri(playlist_name):
    results = sp.search(q=playlist_name, type='playlist')

    playlist_uri = results['playlists']['items'][0]['uri']
    return playlist_uri


def get_albums(artist):
    artist_url = get_artist_uri(artist)
    results = sp.artist_albums(artist_url, album_type='album')
    albums = results['items']
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])

    for album in albums:
        print(album['name'])

    return albums


def get_tracks(artist, limit=10):
    artist_uri = get_artist_uri(artist)
    results = sp.artist_top_tracks(artist_uri)

    for track in results['tracks'][:limit]:
        print('track    : ' + track['name'])
        print('audio    : ' + track['preview_url'])
        print('cover art: ' + track['album']['images'][0]['url'])
        print()


def get_artist_image(artist):
    results = sp.search(q=artist, type='artist')
    items = results['artists']['items']
    ret = items[0]['images'][0]['url']
    print("Artist Image URL:", ret)
    return ret


def get_saved_tracks(limit=50):
    results = sp.current_user_saved_tracks(limit=limit)
    for idx, item in enumerate(results['items']):
        track = item['track']
        print(idx, track['artists'][0]['name'], " : ", track['name'])


def get_top_artists(limit=50, term='short'):
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-top-read',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)

    results = sp.current_user_top_artists(limit=limit, time_range=f'{term}_term')
    for idx, item in enumerate(results['items']):
        print(idx, item['name'])
    return [item['name'] for _, item in enumerate(results['items'])]


def get_related_artists(artist):
    try:
        artist_uri = get_artist_uri(artist)
        results = sp.artist_related_artists(artist_uri)
        similar_artists = [item['name'] for item in results['artists']]
        return similar_artists
    except spotipy.SpotifyException as e:
        print("An error occurred:", e)
        return []


def get_user_devices():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-read-playback-state',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)

    devices = sp.devices()

    if devices:
        print("Available Devices:")
        ret = {}
        for idx, device in enumerate(devices['devices']):
            print(idx + 1, device['name'], device['type'])
            ret[device['name'] + " " + device['type']] = device['id']
        return ret


def get_playlist_tracks(playlist):
    playlist_uri = sp.search(q=playlist, type="playlist")
    print(playlist_uri)


def start_playback(name, device_type="computer"):
    context_uri = get_artist_uri(name.lower())
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-modify-playback-state',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)

    devices = get_user_devices()
    print(devices)

    device_id = list(devices.values())[0]
    for key in devices.keys():
        if device_type in key.lower():
            device_id = devices[key]

    print(context_uri)
    sp.start_playback(device_id=device_id, context_uri=context_uri)


def stop_playback():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-modify-playback-state',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)

    sp.pause_playback()


def resume_playback():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-modify-playback-state',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    sp.start_playback()


def get_current_playback():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-read-playback-state',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    return sp.current_playback()['item']['uri']


def get_track_artwork_url(track_uri):
    scope = "user-library-read"  # You can adjust the scope as needed
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope=scope,
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)

    track_info = sp.track(track_uri)
    images = track_info['album']['images']

    if images:
        artwork_url = images[0]['url']  # You can choose different sizes by changing the index
        return artwork_url
    else:
        return None


def get_current_artist():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-read-playback-state',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    return sp.current_playback()['item']['artists'][0]['name']


def get_current_track():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(scope='user-read-playback-state',
                                           client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                                           client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                                           redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'))
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    return sp.current_playback()['item']['name']

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/playback', methods=['POST'])
def playback():
    artist_name = request.form['name']
    start_playback(artist_name)
    time.sleep(1)
    track_uri = get_current_playback()
    artwork_url = get_track_artwork_url(track_uri)
    current_artist = get_current_artist()
    current_track = get_current_track()

    similar_artists = get_related_artists(current_artist)

    return render_template('index.html', artwork_url=artwork_url,
                           current_artist=current_artist, current_track=current_track, similar_artists=similar_artists)


@app.route('/stop', methods=['POST'])
def stop():
    stop_playback()
    return render_template('index.html', message="Playback stopped!")


@app.route('/resume', methods=['POST'])
def resume():
    resume_playback()
    return render_template('index.html', message="Playback resumed!")


if __name__ == '__main__':
    app.run(debug=True, port=3000)
