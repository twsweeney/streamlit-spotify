import streamlit as st 
import pandas as pd 
import numpy as np 
import os

# from database.loading import create_sqlalchemy_session
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

import plotly.graph_objects as go
import plotly.express as px

from streamlit_utils import *



def get_song_feature_df(session, song_id_list):

    get_songs_query = text('''

    SELECT s.song_id, s.title, s.popularity, s.acousticness, s.danceability, 
                s.energy, s.instrumentalness, s.liveness, s.loudness,
                s.speechiness, s.tempo, s.valence, s.duration_ms, GROUP_CONCAT(a.name SEPARATOR ', ') AS artists
    FROM songs AS s 
    JOIN song_artists AS sa ON s.song_id=sa.song_id
    JOIN artists AS a ON sa.artist_id=a.artist_id
    WHERE s.song_id IN :song_ids
    GROUP BY s.song_id
    ''')

    result = session.execute(get_songs_query, {'song_ids': tuple(song_id_list)})
    rows = result.fetchall()
    song_df = pd.DataFrame(rows, columns=result.keys())

    return song_df







def plot_feature_histogram(session, song_id_list_1, song_id_list_2, feature:str, playlist_name_1:str, playlist_name_2:str):

    get_playlist_1_feature_query = f'''
    SELECT {feature}
    FROM songs
    WHERE song_id IN :song_ids;
    '''
    result = session.execute(text(get_playlist_1_feature_query), {'song_ids': tuple(song_id_list_1)})
    rows = result.fetchall()
    playlist_1_df = pd.DataFrame(rows, columns=result.keys())

    playlist_1_df['source'] = playlist_name_1

    get_playlist_2_feature_query = f'''
    SELECT {feature}
    FROM songs
    WHERE song_id IN :song_ids;
    '''
    result = session.execute(text(get_playlist_2_feature_query), {'song_ids': tuple(song_id_list_2)})
    rows = result.fetchall()
    playlist_2_df = pd.DataFrame(rows, columns=result.keys())

    playlist_2_df['source'] = playlist_name_2



    concat_df = pd.concat([playlist_1_df, playlist_2_df])
    
    if feature == 'duration_ms':
        plotting_df = concat_df.copy()
        plotting_df['duration_seconds'] = plotting_df['duration_ms'] / 1000.0
        feature = 'duration_seconds'
    else:
        plotting_df = concat_df    

    # bin_count = freedman_diaconis_rule(plotting_df[feature])
    bin_count = 20
    fig = px.histogram(plotting_df, x=feature, color='source', histnorm='probability',
                       barmode='overlay', nbins=bin_count,
                       color_discrete_sequence=['orange', 'blue'])
    fig.update_layout(
    title=f"Normalized Histogram of {feature}",
    xaxis_title=feature,
    yaxis_title="Percentage of Total",
    bargap=0.1,  # Adjust gap between bars
    template="plotly_white"
    )
    playlist_1_median = np.nanmedian(playlist_1_df[feature])
    playlist_2_median = np.nanmedian(playlist_2_df[feature])
    return fig, playlist_1_median, playlist_2_median

def display_feature_metrics(feature, playlist_name_1, playlist_name_2, playlist_median_1, playlist_median_2):

    if playlist_median_1 > playlist_median_2:
        more_less = 'more'
        higher_lower = 'higher'
        longer_shorter = 'longer'
    else:
        more_less = 'less'
        higher_lower = 'lower'
        longer_shorter = 'shorter'

    grammar_map = {
        'popularity': f'The songs on {playlist_name_1} are {more_less} popular than the songs than the songs on {playlist_name_2}!', 
        'acousticness': f'The songs on {playlist_name_1} are {more_less} acoustic than the songs on {playlist_name_2}!', 
        'danceability': f'The songs on {playlist_name_1} are {more_less} danceable than the songs on {playlist_name_2}!', 
        'energy': f'The songs on {playlist_name_1} are {more_less} energetic than than the songs on {playlist_name_2}!',
        'instrumentalness': f'The songs on {playlist_name_1} are {more_less} instrumental than the songs on {playlist_name_2}!', 
        'liveness': f'The songs on {playlist_name_1} are {more_less} live than the songs on {playlist_name_2}!', 
        'loudness': f'The songs on {playlist_name_1} are {more_less} loud than the songs on {playlist_name_2}!',
        'speechiness': f'The songs on {playlist_name_1} have {more_less} speechiness than the songs on {playlist_name_2}!',
        'tempo': f'The songs on {playlist_name_1} have {higher_lower} tempo than the songs on {playlist_name_2}!', 
        'valence': f'The songs on {playlist_name_1} have {more_less} valence than the songs on {playlist_name_2}!',
        'duration_ms': f'The songs on {playlist_name_1} are {longer_shorter} than the songs on {playlist_name_2}!'}

    col1, col2 = st.columns(2)
    with col1:
        st.metric(f'{playlist_name_1} Median {feature}', round(playlist_median_1, 3))
    with col2:
        st.metric(f'{playlist_name_2} Median {feature}', round(playlist_median_2, 3))
    st.markdown(grammar_map[feature])
 

def main():
    if 'user_id' not in st.session_state:
        st.markdown('# you are not signed in. Head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]

        st.markdown('# Compare your playlists!')
        st.markdown(f'Currently logged in as: {current_user_display_name}')

        session = create_sqlalchemy_session()

        
        playlist_df = get_playlist_df(session, current_user_id)

        playlist_1_tuple, playlist_2_tuple = display_playlist_selector(playlist_df)
        playlist_id_1, playlist_name_1 = playlist_1_tuple
        playlist_id_2, playlist_name_2 = playlist_2_tuple
        song_id_list_1 = get_song_id_list(session=session, playlist_id=playlist_id_1)
        if playlist_id_2 == None:
            song_id_list_2 = get_song_id_list(session=session, playlist_id=playlist_id_1, exclude=True)
        else:
            song_id_list_2 = get_song_id_list(session=session, playlist_id=playlist_id_2)

        selected_feature = draw_feature_selectbox()
        display_feature_description(selected_feature)
        feature_histogram_fig, playlist_median_1, playlist_median_2 = plot_feature_histogram(session, song_id_list_1=song_id_list_1, song_id_list_2=song_id_list_2,
                                                                                    playlist_name_1=playlist_name_1, playlist_name_2=playlist_name_2, 
                                                                                    feature=selected_feature)
        st.plotly_chart(feature_histogram_fig)
        display_feature_metrics(feature=selected_feature, playlist_name_1=playlist_name_1, playlist_name_2=playlist_name_2,  
                                playlist_median_1=playlist_median_1, playlist_median_2=playlist_median_2)

if __name__ == '__main__':
    main()