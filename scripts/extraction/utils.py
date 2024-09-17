import requests
import csv
import json

def make_session():
    s = requests.session()
    token = api_token
    s.headers = {"Authorization": f"Token {token}"}
    return s

# Function to fetch data from the API endpoint
def fetch_data(url):
    session = make_session()
    response = session.get(url)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return None
    
    return response.json()