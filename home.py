import streamlit as st 
import os
from spotify_api.api import SpotifyAPI
from spotify_api.utils import *
from database.loading import *
import time





def fetch_and_store_data(spotify:SpotifyAPI, app_user_id:str):
    user_playlists = spotify.get_user_playlists()
    playlist_data = extract_playlist_details(user_playlists, app_user_id)
    session = create_sqlalchemy_session()
    load_playlists_data(session, playlist_data)
    playlist_id_list = playlist_data['playlist_id']
    # Create a progress bar
    progress_bar = st.progress(0)
    # Placeholder for displaying the current playlist being processed
    status_text = st.empty()
    # Processeach playlist
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
        if len(playlist_items) == 0:
            # print(f"playlist: {playlist_data['name'][index]} has no songs, skipping to the next playlist")
            continue
        song_data = extract_song_data(playlist_items)
        # print(f'song data extracted successfully')
        # print(f'Loading song data')
        load_song_data(session, song_data)
        # print(f'Extracting song playlist data')
        song_playlist_data = extract_song_playlist_data(playlist_id, playlist_items)
        update_playlist_songs_dates(session, playlist_id,song_playlist_data)
        # print(f'loading song playlist data')
        load_playlists_songs_data(session,  song_playlist_data)

        # print(f'getting songs without audio features')
        null_song_ids_chunked = get_song_ids_with_nulls(session, playlist_id)        
        for chunk in null_song_ids_chunked:
            song_features = spotify.get_audio_features(chunk)
            song_feature_data = extract_song_features_data(song_features)
            load_song_features_data(session, song_feature_data)
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
    progress_bar = st.progress(0)
    # Placeholder for displaying the current playlist being processed
    status_text = st.empty()
    # Processeach playlist
    start_time = time.time()
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
    # st.session_state.clear()
    
    # Usage in Streamlit
    st.title("Spotify API  Authentication")
    
    # print(f' session state: {st.session_state}')

    spotify_api = SpotifyAPI()
    spotify_api.handle_callback()  # Check for the callback and exchange the code for a token

    # Use the Spotify API methods as needed
    if spotify_api.access_token:
        spotify_api.initialize_after_auth()
        user_info = spotify_api.get_current_user()
        st.write("Logged in as user:", spotify_api.display_name)
        st.session_state['display_name'] = spotify_api.display_name
        st.session_state['user_id'] = spotify_api.user_id


        if st.button('Fetch Playlist data!'):
            fetch_and_store_data(spotify=spotify_api, app_user_id=st.session_state['user_id'])




if __name__ == '__main__':
    main()