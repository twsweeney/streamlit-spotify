from sqlalchemy import create_engine, or_, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from streamlit_utils import create_sqlalchemy_session

import os
import numpy as np 
import streamlit as st

from database.sqlalchemy_model import Playlist, Songs, PlaylistSongs, Artist, ArtistGenre, SongArtist
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

# Note that in many of these functions the sqlalchemy session is not closed at the end
# this is intentional, as when these functions are called it is many times in sequence of one another 
# This means we do not have to constantly close and open the sqlalchemy session


def load_playlists_data(session:Session, playlists_data:Dict) -> None:
    '''Loads data into the playlists table using sqlalchemy'''
    n_playlists = len(playlists_data['playlist_id'])
    for i in range(n_playlists):
        new_playlist = Playlist(playlist_id=playlists_data['playlist_id'][i], name=playlists_data['name'][i], 
                                owner_id=playlists_data['owner_id'][i], is_collaborative=playlists_data['is_collaborative'][i], 
                                app_user_id=playlists_data['app_user_id'][i])
        session.add(new_playlist)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()  # Rollback in case of an error
    

def load_song_data(session:Session, song_data:Dict) -> None:
    '''Loads data into the songs table using sqlalchemy'''
    songs = [
        dict(zip(song_data.keys(), values))
        for values in zip(*song_data.values())
    ]
    for song in songs: 
        new_song = Songs(**song)
        if not song['song_id']:
            continue
        session.add(new_song)
        try:
            session.commit()
    
        except IntegrityError:
            session.rollback() # Rollback in case of an error
            
def load_playlists_songs_data(session:Session, song_playlist_data:Dict) -> None:
    '''Loads data into the playlist songs table using sqlalchemy'''
    playlist_songs = [
        dict(zip(song_playlist_data.keys(), values))
        for values in zip(*song_playlist_data.values())
    ]
    for playlist_song in playlist_songs: 

        if not playlist_song['song_id']:
            continue

        new_song = PlaylistSongs(**playlist_song)
        session.add(new_song)
        try:
            session.commit()
        except IntegrityError:
            session.rollback() # Rollback in case of an error


def update_playlist_songs_dates(session:Session, playlist_id, song_playlist_data) -> None:
    '''Updates the playlist table with timestamped information obtained through the songs endpoint'''
    created_date = np.min(song_playlist_data['added_date'])
    last_updated = np.max(song_playlist_data['added_date'])
    updated_playlist = Playlist(playlist_id=playlist_id, created_date=created_date, last_updated=last_updated)
    session.merge(updated_playlist)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()  # Rollback in case of an error

def get_song_ids_with_nulls(session:Session, playlist_id:str, chunk_size=100) -> List:
    '''Gets song ids that are missing data from the audio features endpoint. 
    Returns a list of lists with max  len of 100, since the api endpoint 
    the song ids will be passed to only accepts 100 ids per request'''
    query = f"""
        SELECT s.song_id 
        FROM songs AS s 
        JOIN playlist_songs AS ps ON s.song_id=ps.song_id
        WHERE ps.playlist_id='{playlist_id}' AND 
        s.song_id IS NOT NULL AND
        (acousticness IS NULL 
        OR danceability IS NULL 
        OR energy IS NULL 
        OR instrumentalness IS NULL 
        OR liveness IS NULL 
        OR loudness IS NULL 
        OR speechiness IS NULL 
        OR tempo IS NULL 
        OR valence IS NULL);
    """
    # Execute the raw SQL query
    result = session.execute(text(query))
    # Fetch all results
    null_song_ids = result.fetchall()
    # put the results in a list for easy loopin 
    null_song_ids = [row[0] for row in null_song_ids]
    null_song_ids_chunked = []
    # Chop the results ito chunks 
    n_chunks = (len(null_song_ids) + chunk_size -1) // chunk_size
    for i in range(n_chunks):
        start_index = i*chunk_size 
        end_index = start_index + chunk_size
        chunk = null_song_ids[start_index:end_index]
        null_song_ids_chunked.append(chunk)    
    return null_song_ids_chunked

def get_artists_with_nulls(session:Session, chunk_size = 50) -> List:
    '''Gets aretist ids where there is no genre information filled in. Returns 
    ids in chunks of specified size since only 50 artist ids can be passed to 
    the endpoint in a single request'''
    query = """
    SELECT a.artist_id 
    FROM artists AS a
    LEFT JOIN artist_genres AS g ON a.artist_id=g.artist_id
    WHERE a.popularity IS NULL
    OR g.genre IS NULL;
    """
    result = session.execute(text(query))
    null_artist_ids = result.fetchall()
    null_artist_ids = [row[0] for row in null_artist_ids]
    # Divide into chunks of specified size 
    null_artist_ids_chunked = []
    n_chunks = (len(null_artist_ids) + chunk_size -1) // chunk_size
    for i in range(n_chunks):
        start_index = i*chunk_size 
        end_index = start_index + chunk_size
        chunk = null_artist_ids[start_index:end_index]
        null_artist_ids_chunked.append(chunk)
    return null_artist_ids_chunked

def load_song_features_data(session:Session, song_features_data:Dict) -> None:
    '''Updates the songs table with data obtained through the audio features endpoint'''
    n_songs = len(song_features_data['song_id'])
    for i in range(n_songs):
        # check edge case of song id being null (this rarely happens with songs still on playlists that have been removed from spotify)
        if not song_features_data['song_id'][i]:
            continue
        song = Songs(song_id=song_features_data['song_id'][i], danceability=song_features_data['danceability'][i],
                     acousticness=song_features_data['acousticness'][i], energy=song_features_data['energy'][i],
                     instrumentalness=song_features_data['instrumentalness'][i], liveness=song_features_data['liveness'][i],
                      loudness=song_features_data['loudness'][i], speechiness=song_features_data['speechiness'][i],
                       tempo=song_features_data['tempo'][i], valence=song_features_data['valence'][i] )
        session.merge(song)
        try:
            session.commit()
        except IntegrityError:
            session.rollback() # Rollback in case of an error

def load_artist_data(session:Session, artist_data:Dict) -> None:
    '''Loads artist id and name into the artists table using sqlalchemy'''

    n_artists = len(artist_data['artist_id'])
    for i in range(n_artists):
        new_artist = Artist(artist_id=artist_data['artist_id'][i], name=artist_data['name'][i])
        if not artist_data['artist_id'][i]:
            continue
        session.add(new_artist)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()  # Rollback in case of an error

def update_artist_popularity(session:Session, artist_genre_popularity_data:Dict) -> None:
    '''Load the artist popularity data into the artists table'''
    n_artists = len(artist_genre_popularity_data['artist_id'])
    for i in range(n_artists):
        if not artist_genre_popularity_data['artist_id'][i]:
            continue
        updated_artist = Artist(artist_id=artist_genre_popularity_data['artist_id'][i], popularity=artist_genre_popularity_data['popularity'][i])
        session.merge(updated_artist)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()  # Rollback in case of an error

def load_artist_genre_data(session:Session, artist_genre_popularity_data:Dict) -> None: 
    '''Load artist genre data into the artist genre table'''
    artist_id_list = artist_genre_popularity_data['artist_id']

    for index, artist_id in enumerate(artist_id_list):
        # catch artist id = None and skip
        if not artist_id:
            continue 
        genre_list = artist_genre_popularity_data['genre_list'][index]
        for genre in genre_list:
            artist_genre_entry = ArtistGenre(artist_id=artist_id, genre=genre)
            session.add(artist_genre_entry)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()  # Rollback in case of an error

def load_song_artist_data(session:Session, artist_data:Dict) -> None:
    ''' Load the song artist data  '''
    n_artists = len(artist_data['artist_id'])
    for i in range(n_artists):
        if not artist_data['artist_id'][i]:
            continue
        new_song_artist = SongArtist(artist_id=artist_data['artist_id'][i], song_id=artist_data['song_id'][i])
        session.add(new_song_artist)
        try:
            session.commit()
            # print(f"Artist {artist_data['name'][i]} added.")
        except IntegrityError:
            session.rollback()  # Rollback in case of an error


def delete_playlist_data(session:Session, app_user_id:str) -> None:
    '''Deletes the playlist data for a given user_id'''
    try:
        # Query to delete playlists with the specified app_user_id
        session.query(Playlist).filter(Playlist.app_user_id == app_user_id).delete(synchronize_session=False)
        session.commit()  # Commit the transaction
        st.markdown(f"Deleted playlists for app_user_id: {app_user_id}")
    except Exception as e:
        session.rollback()  # Roll back the transaction in case of error
        st.markdown(f"Error occurred: {e}")
