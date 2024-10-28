import streamlit as st 
from streamlit_utils import *
import numpy as np 
from spotify_api.api import SpotifyAPI
import time
import re
from fuzzywuzzy import fuzz


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


def get_specific_playlist_songs(session:Session, playlist_id:str, current_user_id:str) -> List[str]:
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

def get_all_songs(session:Session, current_user_id:str) -> List[str]:

    get_song_list_query = f'''
        SELECT song_id, p.playlist_id, p.name AS playlist_name
        FROM playlists AS p 
        JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
        WHERE p.app_user_id='{current_user_id}';
        '''
    result = session.execute(text(get_song_list_query))
    rows = result.fetchall()
    song_id_list = [row[0] for row in rows]
    return song_id_list

def get_all_owned_songs(session:Session, current_user_id:str) -> List[str]:

    get_song_list_query = f'''
        SELECT song_id, p.playlist_id, p.name AS playlist_name
        FROM playlists AS p 
        JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
        WHERE p.app_user_id='{current_user_id}' AND p.owner_id='{current_user_id}';
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

def get_song_data(current_user_id:str, option):
    session = create_sqlalchemy_session()
    playlist_df = get_playlist_df(session, current_user_id)

    # if option == 'Use my liked songs':


    if option == 'Select a specific playlist':
        selected_playlist_id, selected_playlist_name = display_single_playlist_selector(playlist_df)
        st.markdown(f'Selected playlist: {selected_playlist_name}')
        song_id_list = get_specific_playlist_songs(session=session, playlist_id=selected_playlist_id, current_user_id=current_user_id)

    elif option == 'Use all playlists owned by me':
        st.markdown(f'Using all playlists owned by you')
        song_id_list = get_all_owned_songs(session=session, current_user_id=current_user_id)

    else:
        st.markdown(f'Using all playlists you have saved')
        song_id_list = get_all_songs(session=session, current_user_id=current_user_id)



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

def clean_title(title):
    # Convert to lowercase for case-insensitive matching
    lower_title = title.lower()
    
    # Comprehensive pattern for featured artists
    # Handles: feat., feat, featuring, ft., ft, with, &, x, ×, +
    import re
    feat_variations = r"""
        \s*[\(\[]+                    # Opening bracket/parenthesis with optional spaces
        (?:                           # Non-capturing group for all the variations
            feat(?:uring|\.)?\s+|     # feat. featuring, feat
            ft\.?\s+|                 # ft., ft
            with\s+|                  # with
            (?:^|\s+)(?:[x×+&])\s+|  # x, ×, +, & (with spaces)
        )
        .*?                          # The artist name(s)
        [\)\]]+                      # Closing bracket/parenthesis
        |                            # OR (handle without brackets)
        \s+(?:feat(?:uring|\.)?\s+|ft\.?\s+|with\s+|(?:[x×+&])\s+).*?$
    """
    
    title = re.sub(feat_variations, '', title, flags=re.IGNORECASE | re.VERBOSE)
    
    # Try to find the dash with optional spaces
    dash_index = lower_title.find(" - ")
    if dash_index == -1:
        dash_index = lower_title.find("-")
    
    # If we found a dash, check what comes after it
    if dash_index != -1:
        # Extract the part after the dash
        suffix = lower_title[dash_index:]
        
        # Look for year pattern (4 digits) and remaster/remake
        if re.search(r'\b\d{4}\b.*\b(remaster|remake)\b', suffix, re.IGNORECASE):
            # Return the part before the dash, stripped of whitespace
            return title[:dash_index].strip().lower()
    
    # Return the cleaned title, stripped of whitespace
    return title.strip().lower()



def evaluate_answer(song_guess:str, artist_guess:str):

    clean_song_input = clean_title(song_guess)

    clean_artist_input = artist_guess.strip().lower()

    song_answer = clean_title(st.session_state['song_name'])


    clean_artist_list = [artist.strip().lower() for artist in st.session_state['artists_name_list']]

    # Set thresholds
    song_threshold = 80  
    artist_threshold = 80  

    # Check for close matches using fuzzy matching
    song_correct = (fuzz.ratio(clean_song_input, song_answer) >= song_threshold)

    # This will calculate the fuzz ratio for all artists and compare them to the list
    # If the input is not close to anything in the correct answer then this will return -1
    # if it is within the threshold, then this will return the index in the artist list with the match


    fuzz_ratio_artist_list = [fuzz.ratio(clean_artist_input, artist)  for artist in clean_artist_list]
    max_fuzz = max(fuzz_ratio_artist_list)
    max_index = fuzz_ratio_artist_list.index(max_fuzz)

    if max_fuzz < artist_threshold:
        artist_correct = -1
    else:
        artist_correct = max_index



    return song_correct, artist_correct



def highlight_rows(row):
    # Initialize the highlight list for both song and artist
    highlights = [''] * len(row)  # Create a list of empty strings for each column
    
    # Highlight logic for song
    if row['correct_song'] is True:
        highlights[0] = 'background-color: green'  # Green for correct song
    elif row['correct_song'] is False:
        highlights[0] = 'background-color: red'  # Red for incorrect song
        
    # Highlight logic for artist
    if row['correct_artist'] is True:
        highlights[1] = 'background-color: green'  # Green for correct artist
    elif row['correct_artist'] is False:
        highlights[1] = 'background-color: red'  # Red for incorrect artist
    
    return highlights  # Return the list of styles

def display_guess_df():
    raw_df = pd.DataFrame(st.session_state['guess_dictionary'])
    styled_df = raw_df.style.apply(highlight_rows, axis=1)
    st.dataframe(styled_df)

def display_correct_answer():
    n_artists = len(st.session_state['artists_name_list'])
    items = st.session_state['artists_name_list']
    if n_artists == 1:
        artist = items[0]
    else:
        artist = ', '.join(items[:-1]) + ', and ' + items[-1]
    

    st.write(f'The answer was: {st.session_state["song_name"]} by {artist}')




# pick a track
def main():
    if 'user_id' not in st.session_state:
        st.markdown('# you are not signed in. Head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]
        MAX_ROUNDS = 6


        st.markdown('# Heardle')
        # st.markdown(f'Currently logged in as: {current_user_display_name}')

        if 'game_state' not in st.session_state:
            st.session_state['game_state'] = 'start'

        if st.session_state['game_state'] == 'start':
            
            selectbox_options = [ 'Use all playlists owned by me', 'Use all playlists I have saved', 'Select a specific playlist']
            option = st.selectbox(label='Where should songs be selected from?',options=selectbox_options)




            song_data = get_song_data(current_user_id, option)
            st.session_state['audio_url'] = song_data['preview_url']
            st.session_state['song_name'] = song_data['name']
            st.session_state['artists_name_list'] = [artist['name'] for artist in song_data['artists']]

            fill_string = '-' * 50

            st.session_state['guess_dictionary'] = {"song": [fill_string] * MAX_ROUNDS,  
                                                    "artist": [fill_string] * MAX_ROUNDS,  
                                                    "correct_song": [None] * MAX_ROUNDS,
                                                    "correct_artist": [None] * MAX_ROUNDS}


            st.write('Important note: This snippet is not necessarily the start of the song.\n Spotify creates the snippets and they are usually in the middle of a song.')
            if st.button('Click here to start the game!'):
                

                st.session_state['game_state'] = 'guess'
                st.rerun()
            
            
        


        elif st.session_state['game_state'] == 'guess':
            if 'round' not in st.session_state:
                st.session_state['round'] = 1
            st.session_state['correct_guess'] = False


            display_guess_df()


            current_round = st.session_state['round']
            round_durations_map = {
                1:1.5,
                2:3,
                3:8,
                4:14,
                5:20,
                6:30
            }
            snippet_duration = round_durations_map[current_round]
            



            if st.button(f'Play Audio Snippet'):
                play_audio(snippet_duration)
                time.sleep(snippet_duration + 0.5)
                st.rerun()

        
            # st.write(f"Correct answer for debugging: {st.session_state['song_name']} by {st.session_state['artists_name_list']}")
            song_guess = st.text_input("Guess the Song")
            artist_guess = st.text_input("Guess the Artist")

            col1, col2 = st.columns(2)
            with col1:
                if st.button('Submit Answer'):
                    st.session_state['correct_song_answer'], st.session_state['correct_artist_index'] = evaluate_answer(song_guess, artist_guess)

                    # this if else logic is introduced so that if a user misspells an artist name or song within the accepted threshold
                    # Then the answer that will be displayed in the summary table will be the correct spelling, not the inputted misspelling


                    # Check song answer 
                    if st.session_state['correct_song_answer']:
                        st.session_state['guess_dictionary']['song'][current_round-1] = st.session_state['song_name']
                    else:
                        st.session_state['guess_dictionary']['song'][current_round-1] = song_guess 
                    st.session_state['guess_dictionary']['correct_song'][current_round-1] = st.session_state['correct_song_answer']


                    # Check artist answer
                    if st.session_state['correct_artist_index'] >= 0:
                        st.session_state['guess_dictionary']['artist'][current_round-1] = st.session_state['artists_name_list'][st.session_state['correct_artist_index']]
                        st.session_state['guess_dictionary']['correct_artist'][current_round-1] = True
                        st.session_state['correct_artist_answer'] = True
                    else:
                        st.session_state['guess_dictionary']['artist'][current_round-1] = artist_guess
                        st.session_state['guess_dictionary']['correct_artist'][current_round-1] = False
                        st.session_state['correct_artist_answer'] = False

                    # Set state to gameover if this is the last round, or they got it right
                    if current_round == MAX_ROUNDS or (st.session_state['correct_song_answer'] and st.session_state['correct_artist_answer']):
                        st.session_state['game_state'] = 'game_over'
                        st.rerun()

                    else:
                        st.session_state['round'] += 1 
                        st.rerun()
            
            with col2: 
                if st.button('Give up?'):
                    if 'round' in st.session_state:
                        del st.session_state['round']

                    if 'correct_song_answer' not in st.session_state:
                        st.session_state['correct_song_answer'] = False
                    if 'correct_artist_answer' not in st.session_state:
                        st.session_state['correct_artist_answer'] = False
                    
                    st.session_state['game_state'] = 'game_over'
                    st.rerun()

            

        elif st.session_state['game_state'] == 'game_over':

            if st.session_state['correct_song_answer'] and not st.session_state['correct_artist_answer']:
                st.write('You got the song right!')
                st.write('Maybe if you applied yourself you could get the artist right too')
                display_correct_answer()
            elif not st.session_state['correct_song_answer'] and st.session_state['correct_artist_answer']:
                st.write('You got the artist but not the song which is just dissapointing honestly')
                display_correct_answer()
            elif st.session_state['correct_song_answer'] and st.session_state['correct_artist_answer']:
                st.write( 'congrats BUDDY you won...')
                display_correct_answer()
                st.write('but u already knew that... dont get a big head about this')
            else:
                st.write('You lost!!!!!!!!!!!!!!!!')
                display_correct_answer()
            if 'round' in st.session_state:
                del st.session_state['round']

            if st.button('Click here to restart and play again'):
                st.session_state['game_state'] = 'start'
                st.rerun()




if __name__ == '__main__':
    main()




        