# this is where all of the functions that format the data into useful forms for the database will go 
import numpy as np 
from datetime import datetime
from typing import Dict, List, Optional

def extract_playlist_details(user_playlists:List[Dict], app_user_id:str) -> Dict:
    '''takes in get current user playlists response and fills in
    ids and names'''

    n_playlists = len(user_playlists)
    app_user_id_list = [app_user_id] * n_playlists
    playlists_data = {
        'playlist_id':[playlist['id'] for playlist in user_playlists],
        'name':[playlist['name'] for playlist in user_playlists],
        'owner_id':[playlist['owner']['id'] for playlist in user_playlists],
        'is_collaborative':[playlist['collaborative'] for playlist in user_playlists],
        'app_user_id':app_user_id_list

    }
    return playlists_data

def format_release_date(date_str:str) -> Optional[str]:
    '''Handle the different formats of input strings and fill in 1 if there is no value there. '''
    if not date_str:
        return None
    try:
        # Try parsing as full date (YYYY-MM-DD)
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        try:
            # If parsing fails, try parsing as year-month (YYYY-MM)
            date = datetime.strptime(date_str, '%Y-%m')
            # Set the day to the first of the month
            date = date.replace(day=1)
        except ValueError:
            try:
                # If parsing fails, handle year-only (YYYY)
                date = datetime.strptime(date_str, '%Y')
                # Set the month and day to the first of the year
                date = date.replace(month=1, day=1)
            except ValueError:
                return None

    # Return the date in 'YYYY-MM-DD' format
    return date.strftime('%Y-%m-%d')

def extract_song_data(playlist_items:Dict) -> Dict[str, List]:
    '''Format song data into a dictionary of lists'''
    song_data = {
        'song_id':[playlist_item['track']['id'] for playlist_item in playlist_items],
        'title': [playlist_item['track']['name'] for playlist_item in playlist_items],
        'album_name':[playlist_item['track']['album']['name'] for playlist_item in playlist_items],
        'album_id':[playlist_item['track']['album']['id'] for playlist_item in playlist_items],
        'duration_ms':[playlist_item['track']['duration_ms'] for playlist_item in playlist_items],
        'release_date':[format_release_date(playlist_item['track']['album']['release_date']) for playlist_item in playlist_items],
        'popularity':[playlist_item['track']['popularity'] for playlist_item in playlist_items],
    }
    return song_data
    
def extract_song_playlist_data(playlist_id:str, playlist_items:Dict)-> Dict[str, List]:
    '''Foramt song playlist data into a dictionary of lists'''
    song_playlist_data = {
        'playlist_id':[playlist_id] * len(playlist_items),
        'song_id':[playlist_item['track']['id'] for playlist_item in playlist_items],
        'added_date':[datetime.strptime(playlist_item['added_at'], "%Y-%m-%dT%H:%M:%SZ") for playlist_item in playlist_items],
        'added_by':[playlist_item['added_by']['id'] for playlist_item in playlist_items]
    }
    return song_playlist_data

def extract_song_features_data(audio_features_items:Dict)-> Dict[str, List]:
    '''Format the song features into a dictionary of lists'''
    audio_features_array = audio_features_items['audio_features']
    audio_features_clean = []
    for audio_features in audio_features_array:
        try:
            song_id = audio_features['id']
            audio_features_clean.append(audio_features)
        except TypeError:
            continue 
    song_features_data = {
        'song_id':[audio_features_item['id'] for audio_features_item in audio_features_clean],
        'danceability':[audio_features_item['danceability'] for audio_features_item in audio_features_clean],
        'acousticness':[audio_features_item['acousticness'] for audio_features_item in audio_features_clean], 
        'energy':[audio_features_item['energy'] for audio_features_item in audio_features_clean], 
        'instrumentalness':[audio_features_item['instrumentalness'] for audio_features_item in audio_features_clean], 
        'liveness':[audio_features_item['liveness'] for audio_features_item in audio_features_clean],
        'loudness':[audio_features_item['loudness'] for audio_features_item in audio_features_clean], 
        'speechiness':[audio_features_item['speechiness'] for audio_features_item in audio_features_clean], 
        'tempo':[audio_features_item['tempo'] for audio_features_item in audio_features_clean], 
        'valence':[audio_features_item['valence'] for audio_features_item in audio_features_clean]
    }
    return song_features_data

def extract_artist_data(playlist_items) -> Dict[str, List]:
    '''Formats artist data into a dictionary of lists'''
    artist_data = {
        'artist_id':[],
        'name':[], 
        'song_id':[]
    }
    # each item in this array holds the artist array for a single song
    track_objects = [playlist_item['track'] for playlist_item in playlist_items]
    for track_object in track_objects:
        song_id = track_object['id']

        artist_array = track_object['artists']
        for artist in artist_array:
            artist_data['artist_id'].append(artist['id'])
            artist_data['name'].append(artist['name'])
            artist_data['song_id'].append(song_id)
    return artist_data

def extract_artist_genre_popularity_data(artist_genres) -> Dict[str, List]:
    '''Formats artist genre data into a dictionary of lists'''
    artist_data = {
        'artist_id':[],
        'genre_list':[], 
        'popularity':[]
    }
    artist_array = artist_genres['artists']
    for artist in artist_array:
        artist_data['artist_id'].append(artist['id'])
        artist_data['genre_list'].append(artist['genres'])
        artist_data['popularity'].append(artist['popularity'])
    return artist_data


