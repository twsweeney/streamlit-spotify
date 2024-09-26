DROP DATABASE spotify_db;

CREATE DATABASE spotify_db;

USE spotify_db;

-- Create `artists` Table
CREATE TABLE artists (
    artist_id VARCHAR(255) PRIMARY KEY, 
    name VARCHAR(255) NOT NULL,
    popularity FLOAT
);

CREATE TABLE artist_genres (
    artist_id VARCHAR(255), 
    genre VARCHAR(255),
    PRIMARY KEY (artist_id, genre),
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE
);


-- Create `songs` Table
CREATE TABLE songs (
    song_id VARCHAR(255) UNIQUE PRIMARY KEY,  
    title VARCHAR(255) NOT NULL,             
    album_name VARCHAR(255),      
    album_id VARCHAR(255),                  
    duration_ms FLOAT,                           
    release_date DATE,                      
    popularity FLOAT,
    acousticness FLOAT, 
    danceability FLOAT,
    energy FLOAT, 
    instrumentalness FLOAT, 
    liveness FLOAT,
    loudness FLOAT, 
    speechiness FLOAT, 
    tempo FLOAT, 
    valence FLOAT
                    
);

-- Create `song_artists` Table
CREATE TABLE song_artists (
    song_id VARCHAR(255),
    artist_id VARCHAR(255),
    PRIMARY KEY (song_id, artist_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE
);

-- Create `playlists` Table
CREATE TABLE playlists (
    playlist_id VARCHAR(255) UNIQUE PRIMARY KEY,   
    name VARCHAR(255) NOT NULL,                   
    owner_id VARCHAR(255),
    is_collaborative TINYINT(1),
    created_date TIMESTAMP DEFAULT NULL,  
    last_updated TIMESTAMP DEFAULT NULL,
    app_user_id VARCHAR(255)
);
-- Create `playlist_songs` Table
CREATE TABLE playlist_songs (
    playlist_id VARCHAR(255),
    song_id VARCHAR(255),
    added_date TIMESTAMP DEFAULT NULL,
    added_by VARCHAR(255),  
    PRIMARY KEY (playlist_id, song_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(song_id) ON DELETE CASCADE
);