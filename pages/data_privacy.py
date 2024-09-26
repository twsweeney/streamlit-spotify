import streamlit as st 
from database.loading import delete_playlist_data
from streamlit_utils import create_sqlalchemy_session
def main():
    st.markdown('All data is collected through the [Spotify Web API](https://developer.spotify.com/documentation/web-api)')
    

    st.markdown('The only data that is stored by this application is the name of all of your saved playlists and their contents')

    if 'user_id'  in st.session_state:

        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]

        st.markdown(f'Currently logged in as: {current_user_display_name}')

        if st.button(f'Click to delete all playlist data associated with {current_user_display_name}. This cannot be undone!'):
            session = create_sqlalchemy_session()
            delete_playlist_data(current_user_id)
            session.close()
            st.success(f"Data successfully deleted for user: {current_user_display_name}")




if __name__ == '__main__':
    main()