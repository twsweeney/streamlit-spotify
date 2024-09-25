import streamlit as st 
import pandas as pd 
import os

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


def create_sqlalchemy_session():
    load_dotenv()
    username = 'Toomeh'
    password = os.getenv('DB_PASSWORD')
    dbname = 'spotify_db'
    engine = create_engine(f'mysql+pymysql://{username}:{password}@localhost/{dbname}')
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def get_playlist_df(session, current_user_id:str):
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

def display_playlist_selector(df:pd.DataFrame):

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

def get_song_id_list(session, playlist_id:str, exclude=False):
    if exclude:
        get_song_list_query = f'''
        SELECT song_id, p.playlist_id, p.name AS playlist_name
        FROM playlists AS p 
        JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
        WHERE p.playlist_id != '{playlist_id}';
        '''
    else:
        get_song_list_query = f'''
        SELECT song_id, p.playlist_id, p.name AS playlist_name
        FROM playlists AS p 
        JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
        WHERE p.playlist_id = '{playlist_id}';
        '''
    result = session.execute(text(get_song_list_query))
    rows = result.fetchall()
    song_id_list = [row[0] for row in rows]
    return song_id_list

def get_playlist_title(session, playlist_id):
    get_playlist_title_query = f'''
    SELECT name 
    FROM playlists
    WHERE playlist_id = '{playlist_id}';
    '''
    result = session.execute(text(get_playlist_title_query))
    rows = result.fetchall()
    return rows[0][0]