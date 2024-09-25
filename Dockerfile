# Use the official Python 3.11 image
FROM python:3.11

# Set the working directory in the container
WORKDIR /home

# Copy requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8501

# Command to run the app
CMD ["streamlit", "run", "home.py", "--server.port=8501", "--server.address=0.0.0.0"]
