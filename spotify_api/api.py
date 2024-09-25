import requests 
import os 
import time
import streamlit as st
import hashlib
import base64
import random

from streamlit_utils import get_secret, get_ec2_public_ip

class SpotifyAPI:
    def __init__(self):
        
        self.CLIENT_ID = '5ff1fe753a2b4587be0ff3e890cea92f'
        self.CLIENT_SECRET = get_secret('spotify_client_secret')['spotify_client_secret']

        # public_ip = get_ec2_public_ip()
        public_ip = '18.216.76.240'
        if public_ip:
            self.REDIRECT_URI = f"http://{public_ip}:8501/callback"
        else:
            st.error("Could not retrieve public IP.")


        # self.REDIRECT_URI = os.getenv('REDIRECT_URI')
        self.scope = "playlist-read-private"

        # Initialize the access token
        self.access_token = None
        # Attempt to get the access token from the session state
        self.get_access_token()

    def generate_random_string(self, length):
        """Generates a random string of specified length."""
        possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(random.choice(possible) for _ in range(length))

    def start_auth_flow(self):
        """Starts the  authentication flow."""
        
        auth_url = (
            f"https://accounts.spotify.com/authorize"
            f"?response_type=code"
            f"&client_id={self.CLIENT_ID}"
            f"&redirect_uri={self.REDIRECT_URI}"
            f"&scope={self.scope}"
        )

        # Redirect the user to the authorization URL
        st.write(f"[Authorize with Spotify]({auth_url})")


    def get_access_token(self):
        """Retrieves the access token from Streamlit session state or starts the auth flow."""
        if 'access_token' in st.session_state:
            self.access_token = st.session_state['access_token']
        else:
            self.start_auth_flow()

    def exchange_code_for_access(self, code):
        token_url = 'https://accounts.spotify.com/api/token'

        # Base64 encode client_id:client_secret
        auth_header = base64.b64encode(f"{self.CLIENT_ID}:{self.CLIENT_SECRET}".encode()).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'code': code,
            'redirect_uri': self.REDIRECT_URI,
            'grant_type': 'authorization_code'
        }

        response = requests.post(token_url, headers=headers, data=data)
        return response.json()

    def handle_callback(self):
        """Handles the Spotify redirect callback to retrieve the code."""
        try:
            code = st.query_params['code']
            # code = st.experimental_get_query_params()['code'][0]
            self.access_token = self.exchange_code_for_access(code)['access_token']
            st.session_state['access_token'] = self.access_token
        except KeyError:
            st.write('Click the link to log in!')
            # self.start_auth_flow()

    def initialize_after_auth(self):
        self.base_url = 'https://api.spotify.com/v1/'
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        self.user_id = self.get_current_user()['id']
        self.display_name = self.get_current_user()['display_name']



    def get_data(self, endpoint, get_tracks_request=False, multiple_items=True, chunked=False, params=None):
        all_data = []
        seen_ids = set()
        url = self.base_url + endpoint 

        response = requests.get(url, headers=self.headers, params=params)
        response_data = response.json()
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f'429 code, retrying after: {retry_after} seconds')
            time.sleep(retry_after)
            return self.get_data(endpoint, params)
        response.raise_for_status()
        try:
            total = response_data['total']
            limit = response_data['limit']
            if (total == 0) and (limit==0):
                return []
            n_pages = (total + limit + 1) // limit
        except KeyError:
            n_pages = 1 
            limit = None 
            total = None 

        if chunked:
            all_data = response_data
            return all_data
        for i in range(n_pages):
            if limit:
                offset = i * limit
            else:
                offset = 0
            params = {'offset':offset}
            response = requests.get(url, headers=self.headers, params=params)
            response_data = response.json()
            if multiple_items:
                for item_index, item in enumerate(response_data.get('items',[])):
                    item_id = item.get('track', {}).get('id') if get_tracks_request else item.get('id')
                    if item_id not in seen_ids:
                        all_data.append(item)
                        seen_ids.add(item_id)
            # if we enter this else statement we are only returning data from one item such as one song 
            else:
                all_data.append(response_data)
                break
        return all_data

    def get_current_user(self):
        endpoint = 'me'
        url = self.base_url + endpoint
        response = requests.get(url, headers=self.headers)
        response_data = response.json()
        return response_data


    def get_user_playlists(self):
        endpoint = 'me/playlists'
        params = {'limit':50}
        return self.get_data(endpoint, params=params)


    def get_playlist_items(self, playlist_id):
        endpoint = f'playlists/{playlist_id}/tracks'
        params = {'limit':50}
        return self.get_data(endpoint, get_tracks_request=True, params=params)
    
    def get_audio_features(self, song_ids):
        params = {
            'ids': ','.join(song_ids)
        }
        endpoint = f'audio-features'
        return self.get_data(endpoint, get_tracks_request=False, multiple_items=False, chunked=True, params=params)

    def get_artist_genre(self, artist_ids):
        params = {
            'ids': ','.join(artist_ids)
        }
        endpoint = f'artists'
        return self.get_data(endpoint, get_tracks_request=False, multiple_items=False, chunked=True, params=params)

