##################################################
# Download CourtListener data with an API token 
# and save it to a local directory. As of Sep 2024
# CourtListener restricts the number of requests
# to 5000 per day. This is sufficient unless someone
# wants to scrape large amounts of PACER, opinion data

import sys
import os
import requests
import logging
import pandas as pd
import json
import csv

# Libraries I am not sure if I need
from requests.adapters import HTTPAdapter
from datetime import datetime
import hashlib

from urllib.error import HTTPError
import urllib
import urllib.request
import urllib.parse
from http.client import RemoteDisconnected
import threading
from utils import api_token

print("Scraper started!")

class CLscraper:
    BASE_URL = "https://www.courtlistener.com/api/rest/v4/"
    
    '''This class is used to scrape data from CourtListener
    It can be used to download data for education and position data for judges, 
    financial disclosures and dockets using CourtListener's search API
    '''
    def __init__(self, api_token, max_requests_per_hour=5000):
        '''Initializes the class with the API token and the maximum number of requests per hour
        Creates a data directory if it doesn't exist already
        '''
        self.api_token = api_token
        # Keep track of the number of requests made
        self.request_count = 0
        self.max_requests_per_hour = max_requests_per_hour
        self.data_dir = self.set_data_directory()

    def make_session(self, api_token):
        '''Creates a session with the API token
        '''
        s = requests.session()
        token = api_token
        s.headers = {"Authorization": f"Token {token}"}
        return s
    
    def set_data_directory(self):
        '''Creates a data directory if it doesn't exist already
        '''
        # Get the current working directory
        current_dir = os.getcwd()
        # Traverse up to find the root directory
        root_dir = os.path.dirname(current_dir) # in our case, this should take us to 'scripts'
        if 'scripts' in root_dir:
            # Go up one more level
            root_dir = os.path.dirname(root_dir) # this should take us to the root directory
        # Define the data directory relative to root
        data_dir = os.path.join(root_dir, 'data')

        # Create the data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        print(f"Data directory set to {data_dir}")
        return data_dir
    
    def fetch_data(self, endpoint,start_page=None, max_pages=None):
        '''Fetches data from the specified endpoint with flexible pagination handling

        Args:
            endpoint (str): The endpoint to fetch data from
            start_page (int, optional): The page number to start fetching from. Defaults to None.
            max_pages (int, optional): The maximum number of pages to fetch. Defaults to None.
        
        Returns:
            list: A list of data fetched from the endpoint
        '''
        url = f"{self.BASE_URL}{endpoint}/"
        # Initialize an empty list to store the data
        all_data = []
        # Initialize the page number
        


