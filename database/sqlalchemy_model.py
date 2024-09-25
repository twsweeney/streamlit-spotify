from sqlalchemy import Text, Column, String, TIMESTAMP, ForeignKey, PrimaryKeyConstraint, Float, Boolean, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Playlist(Base):
    __tablename__ = 'playlists'
    playlist_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    owner_id = Column(String(255), nullable=False)
    is_collaborative = Column(Boolean, default=False)
    created_date = Column(TIMESTAMP, nullable=True, default=None)
    last_updated = Column(TIMESTAMP, nullable=True, default=None)
    app_user_id = Column(String(255), nullable=False)

class Songs(Base):
    __tablename__ = 'songs'
    
    song_id = Column(String(255), primary_key=True, unique=True)  # Spotify song ID
    title = Column(String(255), nullable=False)  # Song title, cannot be null
    album_name = Column(String(255))  # Album name
    album_id = Column(String(255))  # Album ID
    duration_ms = Column(Float)  # Duration of the song in ms
    release_date = Column(Date)  # Release date of the song
    popularity = Column(Float)
    acousticness = Column(Float)
    danceability = Column(Float)
    energy = Column(Float)
    instrumentalness = Column(Float)
    liveness = Column(Float)
    loudness = Column(Float)  # Corrected from "lousness" to "loudness"
    speechiness = Column(Float)
    tempo = Column(Float)
    valence = Column(Float)

class PlaylistSongs(Base):
    __tablename__ = 'playlist_songs'
    
    playlist_id = Column(String(255), ForeignKey('playlists.playlist_id', ondelete='CASCADE'), nullable=False)
    song_id = Column(String(255), ForeignKey('songs.song_id', ondelete='CASCADE'), nullable=False)
    added_date = Column(TIMESTAMP, default=None, nullable=True)
    added_by = Column(String(255), default=None, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('playlist_id', 'song_id'),
    )

class Artist(Base):
    __tablename__ = 'artists'
    
    artist_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    popularity = Column(Float)

class ArtistGenre(Base):
    __tablename__ = 'artist_genres'
    
    artist_id = Column(String(255), ForeignKey('artists.artist_id', ondelete='CASCADE'), nullable=False)
    genre = Column(String(255), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('artist_id', 'genre'),
    )

class SongArtist(Base):
    __tablename__ = 'song_artists'
    
    song_id = Column(String(255), ForeignKey('songs.song_id', ondelete='CASCADE'), nullable=False)
    artist_id = Column(String(255), ForeignKey('artists.artist_id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('song_id', 'artist_id'),
    )



# class UserToken(Base):
#     __tablename__ = 'user_tokens'
    
#     app_user_id = Column(String(255))      # Unique identifier for the user
#     display_name = Column(String(255))
#     code_verifier = Column(String(255))
#     access_token = Column(Text, nullable=False)                # The user's access token
#     refresh_token = Column(Text, nullable=False)               # The user's refresh token
#     expires_at = Column(DateTime, nullable=False)              # Expiration date and time of the access token
#     created_at = Column(TIMESTAMP, nullable=True, default=TIMESTAMP)  # Timestamp for when the token was created
#     updated_at = Column(TIMESTAMP, nullable=True, default=TIMESTAMP, onupdate=TIMESTAMP)  # Timestamp for when the token was last updated
