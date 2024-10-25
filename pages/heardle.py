import streamlit as st 
from streamlit_utils import *
import numpy as np 
from spotify_api.api import SpotifyAPI
import time


def display_single_playlist_selector(df): 
    filtered_df = df.copy()
    selected_playlist_name = st.selectbox(
        "Compare Playlist:",
        filtered_df['name'] if not filtered_df.empty else ["No Playlists Available"]
        )
    
    selected_playlist = filtered_df[filtered_df['name'] == selected_playlist_name]
    selected_playlist_id = selected_playlist['playlist_id'].values[0]
    st.session_state['round'] = 1
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
    spotify_api.initialize_after_auth()

    track_data = spotify_api.get_track(song_id)
    return track_data
    # st.write(track_data)

def get_song_data(current_user_id:str):
    session = create_sqlalchemy_session()
    playlist_df = get_playlist_df(session, current_user_id)

    selected_playlist_id, selected_playlist_name = display_single_playlist_selector(playlist_df)

    st.markdown(f'Selected playlist: {selected_playlist_name}')
    song_id_list = get_songs(session=session, playlist_id=selected_playlist_id, current_user_id=current_user_id)
    random_index = np.random.randint(0, len(song_id_list))

    random_song_id = song_id_list[random_index]


    song_data = get_audio_preview(random_song_id)
    return song_data

def play_audio(snippet_duration:int):


    html_audio = f"""
    <audio id="audio" src="{st.session_state['audio_url']}" autoplay></audio>
    <script>
    var audio = document.getElementById('audio');
    audio.play();
    setTimeout(() => {{ audio.pause(); }}, {snippet_duration * 1000}); // Stop after {snippet_duration} seconds
    </script>
    """

    # Embed the HTML audio player in Streamlit without controls
    st.components.v1.html(html_audio, height=0)

def evaluate_answer(user_input):
    clean_input = user_input.strip().lower()
    answer = st.session_state['song_name'].strip().lower()

    return clean_input == answer


# pick a track
def main():
    if 'user_id' not in st.session_state:
        st.markdown('# you are not signed in. Head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]
        MAX_ROUNDS = 6


        st.markdown('# Heardle')
        st.markdown(f'Currently logged in as: {current_user_display_name}')

        if 'game_state' not in st.session_state:
            st.session_state['game_state'] = 'start'

        if st.session_state['game_state'] == 'start':
            song_data = get_song_data(current_user_id)
            st.session_state['audio_url'] = song_data['preview_url']
            st.session_state['song_name'] = song_data['name']
            st.session_state['artists_name_list'] = [artist['name'] for artist in song_data['artists']]

            if st.button('Click here to start the game!'):
                st.session_state['game_state'] = 'guess'
                st.rerun()
        


        elif st.session_state['game_state'] == 'guess':
            if 'round' not in st.session_state:
                st.session_state['round'] = 1
            st.session_state['correct_guess'] = False\
            
            round_durations_map = {
                1:2,
                2:5,
                3:10,
                4:15,
                5:20,
                6:30
            }
            snippet_duration = round_durations_map[st.session_state['round']]
            
            st.markdown(f"Currently on round {st.session_state['round']}/{MAX_ROUNDS}")


            if st.button(f'Play {snippet_duration} Second Audio Snippet'):
                play_audio(snippet_duration)
        
            st.write(f"Correct answer for debugging: {st.session_state['song_name']}")
            
            user_guess = st.text_input("Guess the song name and artist (format: Song - Artist):")
            if st.button('Submit Answer'):
                st.session_state['correct_answer'] = evaluate_answer(user_guess)

                # Set state to gameover if this is the last round, or they got it right
                if st.session_state['round'] == MAX_ROUNDS or st.session_state['correct_answer']:
                    st.session_state['game_state'] = 'game_over'
                    st.rerun()

                else:
                    st.session_state['round'] += 1 
                    st.rerun()
                    # st.write(f'Wrong answer! Moving on to round {st.session_state["round"]}/{MAX_ROUNDS}')

            

        elif st.session_state['game_state'] == 'game_over':

            if st.session_state['correct_answer']:
                st.write('You win! congrats BUDDY')
            else:
                st.write('You lost!!!!!!!!!!!!!!!!')
            if 'round' in st.session_state:
                del st.session_state['round']

            if st.button('Click here to restart and play again'):
                st.session_state['game_state'] = 'start'
                st.rerun()




if __name__ == '__main__':
    main()




        