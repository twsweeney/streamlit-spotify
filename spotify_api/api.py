import requests 
import time
import streamlit as st
import base64
import random

from streamlit_utils import get_secret
from typing import List, Dict, Any, Optional

class SpotifyAPI:
    def __init__(self) -> None:
        '''Initializes the SpotifyAPI class with necessary credentials and prepares for OAuth flow.'''

        self.CLIENT_ID = '5ff1fe753a2b4587be0ff3e890cea92f'
        self.CLIENT_SECRET = get_secret('spotify_client_secret')['spotify_client_secret']

        # public_ip = get_ec2_public_ip()
        public_ip = '18.223.158.104'
        if public_ip:
            self.REDIRECT_URI = f"http://{public_ip}:8501/"
        else:
            st.error("Could not retrieve public IP.")


        self.scope = "playlist-read-private"

        # Initialize the access token
        self.access_token = None
        # Attempt to get the access token from the session state
        self.get_access_token()

    def start_auth_flow(self) -> None:
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


    def get_access_token(self) -> None:
        """Retrieves the access token from Streamlit session state or starts the auth flow."""
        if 'access_token' in st.session_state:
            self.access_token = st.session_state['access_token']
        else:
            self.start_auth_flow()

    def exchange_code_for_access(self, code:str) -> Dict[str, Any]:
        '''Take in the authorization code and exchange it for an access code that can be used for api calls.
        Returns a json response containing the access code. '''
        token_url = 'https://accounts.spotify.com/api/token'

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

    def handle_callback(self) -> None:
        """Handles the Spotify redirect callback to retrieve the code."""
        try:
            code = st.query_params['code']
            # code = st.experimental_get_query_params()['code'][0]
            self.access_token = self.exchange_code_for_access(code)['access_token']
            st.session_state['access_token'] = self.access_token
        except KeyError:
            st.write('Click the link to log in!')
            # self.start_auth_flow()

    def initialize_after_auth(self) -> None:
        """Initializes the API after authentication to retrieve the user's info."""
        self.base_url = 'https://api.spotify.com/v1/'
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        self.user_id = self.get_current_user()['id']
        self.display_name = self.get_current_user()['display_name']

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        '''Send a request to the api at the given endpoint. Params can contain anything that needs to be 
        passed to the endpoint, like a list of song or artist ids to return data about.'''
        url = self.base_url + endpoint
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f'Rate limit exceeded. Retrying after {retry_after} seconds')
            time.sleep(retry_after)
            return self._make_request(endpoint, params)

        response.raise_for_status()
        return response.json()

    def _paginate_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, get_tracks: bool = False) -> List[Dict[str, Any]]:
        '''Handle pagination for endpoints that may contain larger amounts of paginated data'''
        all_items = []
        seen_ids = set()
        params = params or {}

        while True:
            data = self._make_request(endpoint, params)
            items = data.get('items', [])

            for item in items:
                item_id = item.get('track', {}).get('id') if get_tracks else item.get('id')
                if item_id not in seen_ids:
                    all_items.append(item)
                    seen_ids.add(item_id)

            if not data.get('next'):
                break

            params['offset'] = params.get('offset', 0) + params.get('limit', 20)

        return all_items

    def get_current_user(self) -> Dict[str, Any]:
        return self._make_request('me')

    def get_user_playlists(self) -> List[Dict[str, Any]]:
        return self._paginate_request('me/playlists', params={'limit': 50})

    def get_playlist_items(self, playlist_id: str) -> List[Dict[str, Any]]:
        return self._paginate_request(f'playlists/{playlist_id}/tracks', params={'limit': 50}, get_tracks=True)

    # No need to paginate these requests since we are passing in a certain number of ids in the params argument
    def get_audio_features(self, song_ids: List[str]) -> Dict[str, Any]:
        return self._make_request('audio-features', params={'ids': ','.join(song_ids)})

    def get_artist_genre(self, artist_ids: List[str]) -> Dict[str, Any]:
        return self._make_request('artists', params={'ids': ','.join(artist_ids)})

    