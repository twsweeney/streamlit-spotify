import streamlit as st 
import pandas as pd 
import numpy as np 
import os
import json
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker, Session 
import boto3
from botocore.exceptions import ClientError
import requests
from typing import Dict, Any, Tuple, Optional, List


def get_secret(secret_name:str) -> Dict[str, Any]:
    '''Retreives a secret from aws'''
    region_name = "us-east-2"
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
def create_sqlalchemy_session() -> Session:
    '''Creates a sqlalchemy session by connecting to the aws database'''
    database_secret_name = 'rds!db-60329a4c-380a-4809-bcf5-2689a1a604c0'
    database_credentials = get_secret(database_secret_name)
    username = database_credentials['username']
    password = database_credentials['password']
    dbname = 'spotify_db'
    endpoint = 'streamlit-spotify-db.cv2w6ig8qy6y.us-east-2.rds.amazonaws.com'
    engine = create_engine(f'mysql+pymysql://{username}:{password}@{endpoint}/{dbname}')
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def get_playlist_df(session, current_user_id:str) -> pd.DataFrame:
    '''Gets all playlists for the current app user'''
    get_available_playlists_query = f'''
    SELECT playlist_id, name, owner_id, is_collaborative
    FROM playlists
    WHERE app_user_id = '{current_user_id}'
    ORDER BY last_updated DESC;
    '''
    result = session.execute(text(get_available_playlists_query))
    rows = result.fetchall()
    playlist_df = pd.DataFrame(rows, columns=result.keys())
    return playlist_df 

def display_playlist_selector(df:pd.DataFrame) -> Tuple[Tuple[Optional[str], str], Tuple[Optional[str], str]]:
    '''Dislays two dropdowns to select playlist names from'''
    filtered_df = df.copy()
    col1, col2 = st.columns(2)
    with col1:
        selected_playlist_name_1 = st.selectbox(
        "Compare Playlist:",
        filtered_df['name'] if not filtered_df.empty else ["No Playlists Available"]
        )

    intermediate_df = filtered_df[filtered_df['name'] != selected_playlist_name_1]
    # Create a list of options for the second selectbox
    second_playlist_options = list(intermediate_df['name']) if not filtered_df.empty else ["No Playlists Available"]

    # Add the "Compare to all playlists" default option
    second_playlist_options.insert(0, "All Playlists")

    with col2:
        selected_playlist_name_2 = st.selectbox(
        "To:",
        second_playlist_options
        )

    selected_playlist_1 = filtered_df[filtered_df['name'] == selected_playlist_name_1]
    selected_playlist_id_1 = selected_playlist_1['playlist_id'].values[0]

    if selected_playlist_name_2 == 'All Playlists':
        selected_playlist_id_2 = None
    else:
        selected_playlist_2 = filtered_df[filtered_df['name'] == selected_playlist_name_2]
        selected_playlist_id_2 = selected_playlist_2['playlist_id'].values[0]
    
    return (selected_playlist_id_1, selected_playlist_name_1), (selected_playlist_id_2, selected_playlist_name_2)

def get_song_id_list(session:Session, playlist_id:str, current_user_id:str, exclude=False) -> List[str]:
    '''Gets the song id for the given playlist id. If exclude is set to true then 
    this returns the song id for all playlists except the one specified. This functionality is useful 
    for when comparing one playlist to all other playlists'''
    if exclude:
        get_song_list_query = f'''
        SELECT song_id, p.playlist_id, p.name AS playlist_name
        FROM playlists AS p 
        JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
        WHERE p.playlist_id != '{playlist_id}' AND p.app_user_id={current_user_id};
        '''
    else:
        get_song_list_query = f'''
        SELECT song_id, p.playlist_id, p.name AS playlist_name
        FROM playlists AS p 
        JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
        WHERE p.playlist_id = '{playlist_id}'AND p.app_user_id={current_user_id};
        '''
    result = session.execute(text(get_song_list_query))
    rows = result.fetchall()
    song_id_list = [row[0] for row in rows]
    return song_id_list

def get_playlist_title(session:Session, playlist_id:str) -> str:
    '''Get the title of a specified playlist'''
    get_playlist_title_query = f'''
    SELECT name 
    FROM playlists
    WHERE playlist_id = '{playlist_id}';
    '''
    result = session.execute(text(get_playlist_title_query))
    rows = result.fetchall()
    return rows[0][0]

def check_if_user_exists(session:Session, user_id:str) -> bool:
    '''Checks if the given user is found in the playlist table. 
    Returns true if the user is found in the database'''
    find_user_query = f'''
    SELECT DISTINCT app_user_id 
    FROM playlists
    WHERE app_user_id = '{user_id}';
    '''
    result = session.execute(text(find_user_query))

    user = result.fetchone()
    # if the query has returned nothing, this means the user is not in the DB and user will be set to None and we should return False
    if not user:
        return False
    else:
        return True


def display_feature_description(feature:str) -> None:
    '''Display a dropdown that can be expanded to show the definition of each feature'''
    feature_to_description = {
        'popularity':'The popularity of a track is a value between 0 and 100, with 100 being the most popular. The popularity is calculated by algorithm and is based, in the most part, on the total number of plays the track has had and how recent those plays are.', 
        'acousticness':'A confidence measure from 0.0 to 1.0 of whether the track is acoustic.', 
        'danceability':'Danceability describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable.', 
        'energy':'Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy.', 
        'instrumentalness':'Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly "vocal". The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content. ', 
        'liveness':'Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live.', 
        'loudness':'The overall loudness of a track in decibels (dB). Values closer to zero are louder, for example -5dB is louder than -10dB.',
        'speechiness':'Speechiness detects the presence of spoken words in a track.', 
        'tempo':'The overall estimated tempo of a track in beats per minute (BPM). ', 
        'valence':'A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).',
        'duration_ms':'The duration of the song in units of seconds'}
    with st.expander("Click here to see details about the selected feature"):
        st.write(feature_to_description[feature])

def draw_feature_selectbox() -> str:
    '''Display the feature selectbox'''
    features = ['popularity', 'duration_seconds', 'acousticness', 'danceability', 
             'energy', 'instrumentalness', 'liveness', 'loudness',
             'speechiness', 'tempo', 'valence']
    label = 'What feature would you like to see?'
    option = st.selectbox(label=label, options=features)
    if option == 'duration_seconds':
        option = 'duration_ms'
    return option
