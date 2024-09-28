import streamlit as st 
import os
from spotify_api.api import SpotifyAPI
from spotify_api.utils import *
from database.loading import *
from streamlit_utils import check_if_user_exists
import time

def fetch_and_store_data(spotify:SpotifyAPI, app_user_id:str) -> None:
    user_playlists = spotify.get_user_playlists()
    playlist_data = extract_playlist_details(user_playlists, app_user_id)
    session = create_sqlalchemy_session()
    # save all user playlist data to the database
    load_playlists_data(session, playlist_data)
    playlist_id_list = playlist_data['playlist_id']
    total_playlists = len(playlist_id_list)


    # track_counts = [spotify.get_playlist_track_count(playlist_id) for playlist_id in playlist_id_list]
    # median_tracks = np.median(track_counts)
    # Create a status bar and text
    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()
    total_playlists = len(playlist_id_list)
    remaining_time = None
    for index, playlist_id in enumerate(playlist_id_list):
        
        playlist_name = playlist_data['name'][index]        
        # Update the status text
        if remaining_time:
            status_text.text(f"Getting data for playlist: {playlist_name} \n(Estimated time remaining: {int(remaining_time)} seconds)")
        else:
            status_text.text(f"Getting data for playlist: {playlist_name}")
        playlist_items = spotify.get_playlist_items(playlist_id)
        # if a playlist has no songs on it, skip it
        if len(playlist_items) == 0:
            continue
        # call the api for song data and store in the database

        song_data = extract_song_data(playlist_items)
        load_song_data(session, song_data)

        # Load data into the playlist songs table
        # Playlist songs links together the relationship between a playlist and the songs on it
        # This is a many to many relationship as one song can be on multiple playlists, and one playlist can have multiple songs

        song_playlist_data = extract_song_playlist_data(playlist_id, playlist_items)
        update_playlist_songs_dates(session, playlist_id,song_playlist_data)
        load_playlists_songs_data(session,  song_playlist_data)

        # Since some song feature data is located at a different endpoint in the spotify api, it must be collected seprately
        # First I check the database to see if the data we need is already in the database 

        null_song_ids_chunked = get_song_ids_with_nulls(session, playlist_id)        
        for chunk in null_song_ids_chunked:
            song_features = spotify.get_audio_features(chunk)
            song_feature_data = extract_song_features_data(song_features)
            load_song_features_data(session, song_feature_data)
        # Get the artist data for each song and upload it to the database

        artist_data = extract_artist_data(playlist_items)
        load_artist_data(session, artist_data)
        load_song_artist_data(session, artist_data)
        # Update progress bar
        progress = (index + 1) / total_playlists
        progress_bar.progress(progress)
        # Estimate time remaining
        elapsed_time = time.time() - start_time
        estimated_total_time = elapsed_time / (index + 1) * total_playlists
        remaining_time = estimated_total_time - elapsed_time
    status_text.text('Finished processing playlist data, filling in artist genre data now...')
    progress_bar = st.progress(0)
    # Processeach playlist
    start_time = time.time()
    # Get artists without data associated with them yet to be filled in
    null_artist_ids_chunked = get_artists_with_nulls(session)
    n_chunks = len(null_artist_ids_chunked)
    remaining_time = None
    for index, chunk in enumerate(null_artist_ids_chunked):
        if remaining_time:
            status_text.text(f"Filling in artist genre data \n(Estimated time remaining: {int(remaining_time)} seconds)")
        else:
            status_text.text(f"Filling in artist genre data")
        artist_genres = spotify.get_artist_genre(chunk)
        artist_genre_popularity_data = extract_artist_genre_popularity_data(artist_genres)
        update_artist_popularity(session, artist_genre_popularity_data)
        load_artist_genre_data(session, artist_genre_popularity_data)
        # Update progress bar
        progress = (index + 1) / n_chunks
        progress_bar.progress(progress)
        # Estimate time remaining
        elapsed_time = time.time() - start_time
        estimated_total_time = elapsed_time / (index + 1) * n_chunks
        remaining_time = estimated_total_time - elapsed_time
    session.close()
    # Completion message
    st.success("Data processing complete!")

def main():
    
    # Usage in Streamlit
    st.markdown(" # Welcome to my Spotify Playlist analysis app!")
    st.markdown('To see your stats, authenticate through spotify with the link below!')
    spotify_api = SpotifyAPI()
    spotify_api.handle_callback()  # Check for the callback and exchange the code for a token
    # Use the Spotify API methods as needed
    if spotify_api.access_token:
        spotify_api.initialize_after_auth()
        st.write("Logged in as user:", spotify_api.display_name)
        st.session_state['display_name'] = spotify_api.display_name
        st.session_state['user_id'] = spotify_api.user_id
        st.session_state['access_token'] = spotify_api.access_token
        
        status_text = st.markdown('Searching for you in the database...')
        session = create_sqlalchemy_session()
        user_exists = check_if_user_exists(session, spotify_api.user_id)
        session.close()
        # function returns a bool of if the user is in db or not
        if user_exists:
            status_text.markdown('You are in the database! Feel free to update your data by pressing the button below \n or move on to an analysis page on the sidebar!')
        else:
            status_text.markdown('No data found for you, please press the button below!')
        if st.button('Fetch Playlist data!'):
            fetch_and_store_data(spotify=spotify_api, app_user_id=st.session_state['user_id'])
        st.markdown('Note that if you refresh or close the page you wil need to reauthenticate with spotify on the main page')
        st.markdown('For more information about how your data is stored and managed, see the data privacy page')
    else:
        st.markdown('Want to see how it works before logging in? Press the button below to login as the creator of this site (twsweeney). Please just promise not to judge my music taste :)')
        if st.button('Login as test user'):
            st.session_state['user_id'] = 'twsweeney'
            st.session_state['display_name'] = 'twsweeney'
            st.markdown('You are successfully logged in as twsweeney! To log out and log in as yourself, refresh the website and authenticate at the top of the home page.')
            st.markdown('Navagate to one of the pages in the sidebar to see some playlist analysis')
            
    st.markdown('Feel free to check out the "about" page in the sidebar for more information about this site!')
    
if __name__ == '__main__':
    main()