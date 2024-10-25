import streamlit as st 
from streamlit_utils import *
import numpy as np 
from spotify_api.api import SpotifyAPI


def display_single_playlist_selector(df): 
    filtered_df = df.copy()
    selected_playlist_name = st.selectbox(
        "Compare Playlist:",
        filtered_df['name'] if not filtered_df.empty else ["No Playlists Available"]
        )
    
    selected_playlist = filtered_df[filtered_df['name'] == selected_playlist_name]
    selected_playlist_id = selected_playlist['playlist_id'].values[0]

    return selected_playlist_id, selected_playlist_name


def get_songs(session:Session, playlist_id:str, current_user_id:str) -> List[str]:
    get_song_list_query = f'''
        SELECT song_id, p.playlist_id, p.name AS playlist_name
        FROM playlists AS p 
        JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
        WHERE p.playlist_id = '{playlist_id}' AND p.app_user_id='{current_user_id}';
        '''
    result = session.execute(text(get_song_list_query))
    rows = result.fetchall()
    song_id_list = [row[0] for row in rows]
    return song_id_list

def get_audio_preview(song_id:str) -> str:
    spotify_api = SpotifyAPI()

    track_data = spotify_api.get_track(song_id)
    return track_data
    # st.write(track_data)


# pick a track
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

        selected_playlist_id, selected_playlist_name = display_playlist_selector(playlist_df)

        st.markdown(f'Selected playlist: {selected_playlist_name}')
        song_id_list = get_songs(session=session, playlist_id=selected_playlist_id, current_user_id=current_user_id)
        random_index = np.random.randint(0, len(song_id_list))

        random_song_id = song_id_list[random_index]


        song_data = get_audio_preview(random_song_id)
        st.write(song_data)









        