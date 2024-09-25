import streamlit as st 
from streamlit_utils import * 



def get_playlist_averages(session,current_user_id:str) -> pd.DataFrame:

    get_playlist_averages_query = f'''
    SELECT p.name, AVG(s.popularity) AS average_popularity
    FROM playlists AS p 
    JOIN playlist_songs AS ps ON p.playlist_id=ps.playlist_id
    JOIN songs AS s ON ps.song_id=s.song_id
    WHERE p.app_user_id = '{current_user_id}'
    GROUP BY p.playlist_id;
    '''
    result = session.execute(text(get_playlist_averages_query))
    rows = result.fetchall()
    df = pd.DataFrame(rows, columns=result.keys())
    return df 






def main():
    if 'user_id' not in st.session_state:
        st.markdown('# You are not signed in. Please head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        current_user_display_name = st.session_state["display_name"]

        st.markdown('# Compare your playlists!')
        st.markdown(f'Currently logged in as: {current_user_display_name}')

        session = create_sqlalchemy_session()


        playlist_averages_df = get_playlist_averages(session, current_user_id)

        st.write(playlist_averages_df)


        
        # playlist_df = get_playlist_df(session, current_user_id)



if __name__ == '__main__':
    main()