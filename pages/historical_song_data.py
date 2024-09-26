from streamlit_utils import *
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta



def get_song_df(session, current_user_id:str):
    get_available_playlists_query = f'''
    SELECT s.song_id AS song_id, ps.added_date AS added_date, s.duration_ms, 
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
def filter_data(df, days):
    if days is not None:
        start_date = datetime.now() - timedelta(days=days)
        filtered_df = df[df['added_date'] >= start_date]
    else:
        filtered_df = df  # For "All time"
    return filtered_df

# Function to dynamically bin the dates based on the time range
def dynamic_bins(df, days):
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

    # Create a new column for binning
    df['date_bin'] = df['added_date'].dt.to_period(bin_freq).dt.to_timestamp()
    return df

# Function to calculate median popularity over time
# def calculate_median(df, selected_feature):
#     median_popularity = df.groupby('date_bin')[selected_feature].median().reset_index()
#     return median_popularity

def calculate_median(df, days, selected_feature):
    # Group by date_bin and calculate median popularity and song count
    summary = df.groupby('date_bin').agg(
        median_popularity=(selected_feature, 'median'),
        song_count=(selected_feature, 'size')
    ).reset_index()

    # Get the full range of bins, filling missing bins with NaN
    full_range = pd.date_range(start=df['added_date'].min(), 
                               end=df['added_date'].max(), 
                               freq=pd.infer_freq(df['date_bin']))
    
    # Reindex the summary DataFrame to include all bins and introduce NaNs for missing bins
    summary = summary.set_index('date_bin').reindex(full_range).reset_index()
    summary.columns = ['date_bin', 'median_popularity', 'song_count']

    # Fill missing song_count values with 0 (since no songs were added in those periods)
    summary['song_count'].fillna(0, inplace=True)

    # Fill missing median_popularity with NaN (no interpolation, just leave them as NaN)
    return summary

def draw_time_range_selector():
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
    return days

def main():

    if 'user_id' not in st.session_state:
        st.markdown('# you are not signed in. Head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]

        st.markdown('# Compare your playlists!')
        st.markdown(f'Currently logged in as: {current_user_display_name}')

        session = create_sqlalchemy_session()

        song_df = get_song_df(session, current_user_id)

        selected_feature = draw_feature_selectbox()
        display_feature_description(selected_feature)
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
        median_data = calculate_median(binned_data, days, selected_feature)

            # Plot the result using Plotly
        ylabel = 'median_' + selected_feature
        fig = px.line(median_data, x='date_bin', y=ylabel,
                    title=f'Median Song {selected_feature} over Time ({selected_range})',
                    labels={'date_bin': 'Date Added', selected_feature: f'Median {selected_feature}'},
                    hover_data={'song_count': True})  # Include song count on hover

        # Customize hover template to show song count
        trace_label = 'Median ' + selected_feature
        hover_template_string = '<b>Date</b>: %{x}<br><b>' + trace_label + '</b>: %{y}<br><b>Songs Added</b>: %{customdata[0]}'
        fig.update_traces(hovertemplate=hover_template_string)


        # st.write(song_df)



if __name__ == '__main__':
    main()