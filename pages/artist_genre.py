from streamlit_utils import *
import plotly.graph_objects as go
import plotly.express as px

from typing import List
from sqlalchemy.orm import Session


def get_artist_genre_df(session:Session, song_id_list:List) -> pd.DataFrame:
    '''Get the artist genres for all given songs in song_id list'''
    get_artist_genres_query = '''
    SELECT ag.genre AS genre, a.name AS name
    FROM songs AS s 
    JOIN song_artists AS sa ON s.song_id=sa.song_id
    JOIN artists AS a ON sa.artist_id=a.artist_id
    JOIN artist_genres AS ag ON  sa.artist_id=ag.artist_id
    WHERE s.song_id IN :song_ids
    '''
    result = session.execute(text(get_artist_genres_query), {'song_ids': tuple(song_id_list)})
    rows = result.fetchall()
    artist_genre_df = pd.DataFrame(rows, columns=result.keys())
    return artist_genre_df

def plot_artist_genres(df:pd.DataFrame, playlist_title:str) -> go.Figure:
    genre_counts = df['genre'].value_counts().head(10)
    fig = go.Figure(go.Bar(
        x=genre_counts.values,
        y=genre_counts.index,
        orientation='h'
    ))
    fig.update_layout(
        title=f'Top 10 Artist Genres in Playlist: {playlist_title}',
        xaxis_title='Count',
        yaxis_title='Genre', 
        yaxis=dict(autorange='reversed'),
        template='plotly_white'
    )
    return fig

def main():
    if 'user_id' not in st.session_state:
        st.markdown('## You are not signed in. Head back to the home page to sign in!')
    else:
        current_user_id = st.session_state['user_id']
        st.markdown('# Compare the top artist genres in your playlists!')
        st.markdown(f'Currently logged in as: {st.session_state["display_name"]}')

        session = create_sqlalchemy_session()
        # Get all possible playlists to display
        playlist_df = get_playlist_df(session, current_user_id)
        # display and get results from playlist selector 
        playlist_1_tuple, playlist_2_tuple = display_playlist_selector(playlist_df)
        playlist_id_1, playlist_name_1 = playlist_1_tuple
        playlist_id_2, playlist_name_2 = playlist_2_tuple
        song_id_list_1 = get_song_id_list(session=session, playlist_id=playlist_id_1, current_user_id=current_user_id)
        if playlist_id_2 == None: # if playlist 2 is none then we are comparing to all other playlists
            song_id_list_2 = get_song_id_list(session=session, playlist_id=playlist_id_1, current_user_id=current_user_id, exclude=True)
        else:
            song_id_list_2 = get_song_id_list(session=session, playlist_id=playlist_id_2, current_user_id=current_user_id)
        # Get the artist genre data from each selected playlist and plot
        artist_genre_df_1 = get_artist_genre_df(session, song_id_list_1)
        artist_genre_df_2 = get_artist_genre_df(session, song_id_list_2)
        fig1 = plot_artist_genres(artist_genre_df_1, playlist_title=playlist_name_1)
        st.plotly_chart(fig1, use_container_width=True)
        fig2 = plot_artist_genres(artist_genre_df_2, playlist_title=playlist_name_2)
        st.plotly_chart(fig2, use_container_width=True)



if __name__ == '__main__':
    main()