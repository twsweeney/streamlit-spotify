import streamlit as st 
from database.loading import delete_playlist_data
from streamlit_utils import create_sqlalchemy_session
def main():
    st.markdown('All data is collected through the [Spotify Web API](https://developer.spotify.com/documentation/web-api)')
    

    st.markdown('The only data that is stored by this application is the name of all of your saved playlists and their contents')

    st.markdown('This data is stored within an AWS database and is secured using all recommended security practices')

    if 'user_id'  in st.session_state:

        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]

        
        
        if 'access_token' not in st.session_state:
            st.markdown('If you log in then you will be able to delete your data here at any time. ')
        else:
            st.markdown(f'Currently logged in as: {current_user_display_name}')
            st.markdown(f'If you would like to delete data associated with your account, click the button below')
            if st.button(f'Click to delete all playlist data associated with {current_user_display_name}. This cannot be undone!'):
                session = create_sqlalchemy_session()
                delete_playlist_data(session, current_user_id)
                session.close()
                st.success(f"Data successfully deleted for user: {current_user_display_name}")
                st.markdown('Feel free to redownload your data on the homepage at any time!')




if __name__ == '__main__':
    main()