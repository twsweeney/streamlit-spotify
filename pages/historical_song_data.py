from streamlit_utils import *


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
    return playlist_df 



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

        st.write(song_df)



