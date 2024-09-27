# streamlit-spotify

A web application that provides personalized insights into a user's Spotify listening habits. Built with Python, Streamlit, and hosted on AWS EC2.

## See it in action!

To explore the site yourself and enter your own data check out the link below! 

(streamlit-site)[ec2-18-223-158-104.us-east-2.compute.amazonaws.com:8501]

## Features
- Spotify authentication
- Retrieval and storage of user's Spotify data
- Deletion of user data upon request
- Visualization of playlist insights

## Technologies Used
- Python
- Streamlit
- Docker
- AWS EC2
- MySQL database hosted on AWS RDS
- Spotify API

## Architecture Overview
This application is containerized using Docker and hosted on an AWS EC2 instance. It uses a MySQL database (hosted on AWS RDS) for data storage. The frontend is built with Streamlit, providing an interactive user interface.

## Want to recreate the site?
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a mysql database by locally installing mysql or using a cloud hosted option like AWS. 
4. Register a new app in the spotify developer portal.
5. Replace the database and spotify credentials found in api.py with your own. 
6. replace the redirect uri with the public ip address of your ec2 instance, or localhost if testing locally
7. Use the docker build and docker run commands to build the image and start the site! 



