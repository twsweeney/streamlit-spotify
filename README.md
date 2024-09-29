# streamlit-spotify

A web application that provides personalized insights into a user's Spotify listening habits. Built with Python, Streamlit, and hosted on AWS EC2.

## See it in action!

To explore the site yourself and enter your own data check out the link below! 

[Visit the Streamlit App](http://ec2-18-223-158-104.us-east-2.compute.amazonaws.com:8501)

## Features
- Spotify Authentication: Secure login with Spotify.
- Data Retrieval and Storage: Fetches and stores user’s Spotify data.
- Data Deletion: Users can request to have their data deleted.
- Playlist Insights: Visualizes data-driven insights on playlists.

## Technologies Used
- Python
- Streamlit
- Docker
- AWS EC2
- MySQL database hosted on AWS RDS
- Spotify API

## Architecture Overview
This application is containerized using Docker and hosted on an AWS EC2 instance. It uses a MySQL database (hosted on AWS RDS) for data storage. The frontend is built with Streamlit, providing an interactive user interface.

### spotify_api Directory

In this directory there is a class within api.py that handles interactions with the spotify web api and user authenticaiton. There are also some shared functions throughout the project as well as data formatting found in utils.py

### database Directory

This directory contains the sql schema as well as the corresponding sqlalchemy schema. It also contains the functions used to load data into the database within the file loading.py

### pages Directory

Each .py file in this directory contains the script for each page on the streamlit site. 

### Misc

#### Dockerfile and requirements

The dockerfile was used to setup the docker environment that the site is run in. Requirements.txt contains the python dependancies for this project.

#### streamlit utils and home.py

streamlit_utils.py contains functions that are used by all or many of the streamlit pages scripts. 

home.py is the script for the homepage of the streamlit site.

## Want to recreate the site?
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a mysql database by locally installing mysql or using a cloud hosted option like AWS. Run the mysql_schema.sql script to create the database. 
4. Register a new app in the spotify developer portal.
5. Replace the database and spotify credentials found in api.py with your own. 
6. replace the redirect uri with the public ip address of your ec2 instance, or localhost if testing locally
7. Use the docker build and docker run commands to build the image and start the site! 