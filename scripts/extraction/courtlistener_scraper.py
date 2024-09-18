##################################################
# Download CourtListener data with an API token 
# and save it to a local directory. As of Sep 2024
# CourtListener restricts the number of requests
# to 5000 per day. This is sufficient unless someone
# wants to scrape large amounts of PACER, opinion data

# The CourtListener API documentation can be found at:
# https://www.courtlistener.com/help/api/rest/v3 # This should ideally be updated to v4


import os
from dotenv import load_dotenv
import requests
import logging
import pandas as pd
import json
import csv

# Libraries I am not sure if I need
#from requests.adapters import HTTPAdapter
#from datetime import datetime
#import hashlib
#from urllib.error import HTTPError
#import urllib
#import urllib.request
#import urllib.parse
#from http.client import RemoteDisconnected
#import threading

from utils import get_api_token, log_error_to_file

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
        s = requests.Session()
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
    
    @log_error_to_file # Decorator to log errors to a file, defined in utils.py
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
        page_count = start_page if start_page is not None else 1 # Default to 1 if not provided

        while url and (max_pages is None or page_count < max_pages):
            if self.request_count >= self.max_requests_per_hour:
                print("Maximum number of requests reached. Sleeping for 1 hour.")
                time.sleep(3600)
                self.request_count = 0

            # Make a request to the endpoint
            self.session = self.make_session(self.api_token)
            response = self.session.get(url)
            # Increment the request count
            self.request_count += 1

            if response.status_code != 200:
                print(f"Error:  {response.status_code}, {response.text}")
                break

            data = response.json()
            all_data.extend(data['results']) # CL saves data in a 'results' key which is what we want

            # Check if there are more pages
            if 'next' in data and data['next']:
                url = data['next']
                page_count += 1
            else:
                break
            
        self.save_to_json(all_data, start_page or 1, page_count)
        print(f"Total pages fetched: {page_count} starting from page {start_page or 1}")
        return all_data

    def save_to_json(self, data, start_page, end_page):
        '''Save raw data to a json file
        
        Args:
            data (list): The data to save
            start_page (int): The starting page number
            end_page (int): The ending page number

        Returns:
            None. Prints a message indicating the file has been saved with the page range
        '''
        # Create a filename based on the page range
        filename = os.path.join(self.data_dir, f"{start_page}-{end_page}.json")
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {filename}!")

    def process_data(self, data):
        """
        Process and flatten the data.
        """
        processed_data = []
        for item in data:
            entry = {key: item.get(key, None) for key in item}  # Flatten the dictionary
            processed_data.append(entry)
        print(f"Total number of entries processed: {len(processed_data)}")
        return processed_data

    def save_to_csv(self, data, filename):
        """
        Save the data to a CSV file.
        """
        if not data:
            print("No data to save.")
            return
        
        csv_path = os.path.join(self.data_dir, filename)
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = data[0].keys()  # Get the keys of the first element in the list
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in data:
                writer.writerow(item)
        print(f"Data saved to {csv_path}")        


