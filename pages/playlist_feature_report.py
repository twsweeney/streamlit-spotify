import streamlit as st 
from streamlit_utils import * 
import plotly.express as px 
import plotly.graph_objects as go
from sqlalchemy.orm import Session

def get_playlist_averages(session:Session,current_user_id:str) -> pd.DataFrame:
    '''Get the average of every song feature found across all playlists for the current user'''
    get_playlist_averages_query = f'''
    SELECT p.name AS playlist_name, AVG(s.popularity) AS average_popularity, AVG(s.acousticness) AS average_acousticness, AVG(s.danceability) AS average_danceability, 
                AVG(s.energy) AS average_energy, AVG(s.instrumentalness) AS average_instrumentalness, AVG(s.liveness) AS average_liveness, AVG(s.loudness) AS average_loudness,
                AVG(s.speechiness) AS average_speechiness, AVG(s.tempo) AS average_tempo, AVG(s.valence) AS average_valence, AVG(s.duration_ms) / 1000.0 AS average_duration_seconds
    
    FROM playlists AS p 
    JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
    JOIN songs AS s ON ps.song_id=s.song_id
    WHERE p.app_user_id = '{current_user_id}'
    GROUP BY p.playlist_id;
    '''
    result = session.execute(text(get_playlist_averages_query))
    rows = result.fetchall()
    df = pd.DataFrame(rows, columns=result.keys())
    return df 

def get_selected_feature_df(playlist_averages_df:pd.DataFrame, selected_feature:str) -> pd.DataFrame:
    '''get the dataframe for only the playlist we have selected'''
    column_name = 'average_' + selected_feature 
    selected_feature_df = playlist_averages_df[['playlist_name', column_name]].sort_values(by=column_name, ascending=False)
    return selected_feature_df


def display_feature_histogram(selected_feature_df:pd.DataFrame, selected_feature:str) -> go.Figure:
    ''' Display the histogram of the selected feature '''
    bin_count = 20
    column_name = 'average_' + selected_feature 

    fig = px.histogram(selected_feature_df, x=column_name,  histnorm='probability',
                       barmode='overlay', nbins=bin_count,
                       color_discrete_sequence=['blue'])
    fig.update_layout(
    title=f"Normalized Histogram of {selected_feature}",
    xaxis_title=selected_feature,
    yaxis_title="Percentage of Total Playlists",
    bargap=0.1,  # Adjust gap between bars
    template="plotly_white"
    )
    return fig



def main():
    if 'user_id' not in st.session_state:
        st.markdown('# You are not signed in. Please head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]
        st.markdown('# Playlist Feature report')
        st.markdown(f'Currently logged in as: {current_user_display_name}')
        session = create_sqlalchemy_session()
        playlist_averages_df = get_playlist_averages(session, current_user_id)
        selected_feature = draw_feature_selectbox()
        display_feature_description(selected_feature)
        if selected_feature == 'duration_ms':
            selected_feature ='duration_seconds'
        selected_feature_df = get_selected_feature_df(playlist_averages_df, selected_feature)
        fig = display_feature_histogram(selected_feature_df, selected_feature)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander(f"Clich to see all of the data for {selected_feature}", expanded=False):
            st.write(selected_feature_df)
if __name__ == '__main__':
    main()