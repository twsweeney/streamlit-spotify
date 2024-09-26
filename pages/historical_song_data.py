from streamlit_utils import *
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session



def get_song_df(session:Session, current_user_id:str) -> pd.DataFrame:
    '''Get song feature data for playlists created by the current user. 
    For each song also get the timestamp of when the song was added to the playlist.'''

    get_available_playlists_query = f'''
    SELECT s.song_id AS song_id, ps.added_date AS added_date, s.duration_ms / 1000.0 AS duration_seconds, 
    s.popularity, s.acousticness, s.danceability, s.energy, s.instrumentalness,
    s.liveness, s.loudness, s.speechiness, s.tempo, s.valence
    FROM playlists AS p 
    JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
    JOIN songs AS s ON ps.song_id=s.song_id
    WHERE p.app_user_id = '{current_user_id}' 
    AND p.owner_id = '{current_user_id}' 
    AND ps.added_date IS NOT NULL
    ORDER BY ps.added_date DESC;
    '''
    result = session.execute(text(get_available_playlists_query))
    rows = result.fetchall()
    playlist_df = pd.DataFrame(rows, columns=result.keys())
    playlist_df['added_date'] = pd.to_datetime(playlist_df['added_date'])
    return playlist_df 

# Function to filter data based on selected time range
# days is type annotated as Optional[int] allows days to be either an int or None 
def filter_data(df:pd.DataFrame, days:Optional[int]) -> pd.DataFrame:
    '''Filters data based on a selected time range'''
    if days is not None:
        start_date = datetime.now() - timedelta(days=days)
        filtered_df = df[df['added_date'] >= start_date]
    else:
        filtered_df = df  # For "All time"
    return filtered_df

# Function to dynamically bin the dates based on the time range
def dynamic_bins(df:pd.DataFrame, days:Optional[int]):
    if days is None:  # For "All time"
        bin_freq = 'M'  # Monthly bins
    elif days <= 30:
        bin_freq = 'D'  # Daily bins
    elif days <= 90:
        bin_freq = 'W'  # Weekly bins
    elif days <= 180:
        bin_freq = 'W'  # Weekly bins
    elif days <= 365:
        bin_freq = 'M'  # Monthly bins
    else:
        bin_freq = 'M'  # Monthly bins

    # Use .loc[] to avoid the SettingWithCopyWarning
    df_copy = df.copy()  # Avoid changing the original dataframe
    df_copy.loc[:, 'date_bin'] = df_copy['added_date'].dt.to_period(bin_freq).dt.to_timestamp()
    return df_copy

def calculate_median(df:pd.DataFrame, selected_feature:str) -> pd.DataFrame:
    '''Calculate the median of the selected feature over the given date bins'''
    median_df = df.groupby('date_bin')[selected_feature].median().reset_index()
    return median_df

def draw_time_range_selector() -> Optional[int]:
    '''Draws a selectbox to select the time range'''
    time_range_options = {
        "Past month": 30,
        "Past 3 months": 90,
        "Past 6 months": 180,
        "Past year": 365,
        "All time": None
    }
    selected_range = st.selectbox("Select time range:", list(time_range_options.keys()))
    days = time_range_options[selected_range]
    return days

def main():

    if 'user_id' not in st.session_state:
        st.markdown('# you are not signed in. Head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]

        st.markdown('# See how your playlists have changed over time!')
        st.markdown(f'Currently logged in as: {current_user_display_name}')

        session = create_sqlalchemy_session()

        song_df = get_song_df(session, current_user_id)

        selected_feature = draw_feature_selectbox()

        display_feature_description(selected_feature)
        if selected_feature == 'duration_ms':
            selected_feature = 'duration_seconds'
        # Streamlit UI for selecting the time range
        time_range_options = {
            "Past month": 30,
            "Past 3 months": 90,
            "Past 6 months": 180,
            "Past year": 365,
            "All time": None
        }
        selected_range = st.selectbox("Select time range:", list(time_range_options.keys()))
        days = time_range_options[selected_range]
        # Filter and process the data
        filtered_data = filter_data(song_df, days)
        binned_data = dynamic_bins(filtered_data, days)
        median_data = calculate_median(binned_data, selected_feature)
        # Plot the result using Plotly
        fig = px.line(median_data, x='date_bin', y=selected_feature,
                    title=f'Median Song {selected_feature} over Time ({selected_range})',
                    labels={'date_bin': 'Date Added', selected_feature: f'Median {selected_feature}'})  
        st.plotly_chart(fig)
        st.markdown('This chart reflects the statistics of songs that you added to a playlist that you own at a certain time.\nIt is NOT a reflection of your listening.')



if __name__ == '__main__':
    main()