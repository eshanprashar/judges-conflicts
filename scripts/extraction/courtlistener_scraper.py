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
import time
from utils import get_api_token, log_error_to_file

class APIScraper:
    def __init__(self, base_url, api_token=None, max_requests_per_hour=5000, log_dir="logs"):
        """
        Initialize the APIScraper.

        Args:
            base_url (str): The base URL of the API.
            api_token (str, optional): The API token for authentication. Defaults to None.
            max_requests_per_hour (int, optional): Maximum number of requests allowed per hour. Defaults to 5000.
            log_dir (str, optional): Directory for storing logs. Defaults to "logs".
        """
        self.base_url = base_url
        self.api_token = api_token
        self.max_requests_per_hour = max_requests_per_hour
        self.request_count = 0
        self.session = self.make_session(api_token)
        self.log_dir = log_dir
        self.log_file = None  # Initialize the log file path

        # Create log directory if it does not exist
        os.makedirs(log_dir, exist_ok=True)
    
    @log_error_to_file(log_dir="logs")
    def make_session(self, api_token):
        """
        Create and return a session with the required headers.

        Args:
            api_token (str): The API token for authentication.

        Returns:
            requests.Session: A session object with the appropriate headers.
        """
        session = requests.Session()
        if api_token:
            session.headers.update({"Authorization": f"Token {api_token}"})
        return session
    
    def set_data_directory(self, endpoint):
        '''Creates a data directory for the endpoint if it doesn't exist already
        '''
        # Get the current working directory
        current_dir = os.getcwd()
        # Traverse up to find the root directory
        root_dir = os.path.dirname(current_dir) # in our case, this should take us to 'scripts'
        if 'scripts' in root_dir:
            # Go up one more level
            root_dir = os.path.dirname(root_dir) # this should take us to the root directory
        # Define the data directory relative to root
        data_dir = os.path.join(root_dir,'data',endpoint)

        # Create the data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        print(f"Data directory set to {data_dir}")
        return data_dir
    
    def create_log_file(self, endpoint):
        '''Create a log file for the endpoint
        '''
        log_filename = f"{endpoint}_log.txt"
        log_path = os.path.join(self.log_dir, log_filename)
        self.log_file = log_path

        # Create the file if it doesn't exist, but don't write anything to it
        if not os.path.exists(log_path):
            with open(log_path, 'w') as f:
                pass  # This will create an empty file if it doesn't exist
        print(f"Log file created at {log_path}")

    def log_progress(self, current_page):
        """
        Log the progress of the data fetching process.
        Simple print statement for now. Can be extended to write to a log file.

        Args:
            current_page (int): The current page number.
        """
        print(f"Request successful with code 200! Now, fetching page {current_page}...")
    
    def save_next_url_and_page(self, endpoint, next_url, page_number):
        """Save the next URL and the last successfully fetched page number to the log file.
        """
        with open(self.log_file, 'w') as f:
            f.write(f"Next URL: {next_url}\n")
            f.write(f"Last successfully fetched page: {page_number}\n")
        print(f"Next URL and page number saved to {self.log_file}")


    # Function to get the last page number fetched
    def get_last_page(self, endpoint):
        '''Retrieve the last page number fetched from the log file
        Returns:
        int: The last page number fetched
        '''
        try:
            with open(self.log_file, "r") as f:
                log_content = f.read().strip()
                # The log file contains "Last successfully fetched page: X"
                last_page_line = [line for line in log_content.split('\n') if "Last successfully fetched page" in line]
                if last_page_line:
                    last_page = int(last_page_line[0].split(":")[-1].strip())  # Extract page number
                    return last_page
        except:
            return 1  # Default to start from page 1 if no valid log file is found
        return 1  # Default to start from page 1 if no log file is found


    def get_next_url(self, endpoint):
        """
        Get the next URL from the log file to resume from where we left off.
        """
        try:
            with open(self.log_file, 'r') as f:
                log_content = f.read().strip()
                # The log file contains "Next URL: <url>"
                next_url_line = [line for line in log_content.split('\n') if "Next URL:" in line]
                if next_url_line:
                    next_url = next_url_line[0].split("Next URL: ")[-1].strip()
                    return next_url
        except:
            return None  # Default to None if no valid log file is found
        return None  # Default to None if no log file is found


    @log_error_to_file(log_dir="logs")
    def fetch_data(self, endpoint, params=None,save_after_pages=10):
        """
        Fetch data from the API endpoint with pagination handling.

        Args:
            endpoint (str): The API endpoint to fetch data from.
            params (dict, optional): Additional query parameters for the API request. Defaults to None.
            start_page (int, optional): The page number to start fetching from. Defaults to 1.
            max_pages (int, optional): The maximum number of pages to fetch. Defaults to None.
            save_after_pages (int, optional): Save data to a file after every `save_after_pages` pages. Defaults to 10.

        Returns:
            list: A list of data fetched from the API endpoint.
        """
        self.create_log_file(endpoint)  # Create a log file for the endpoint
        next_url = self.get_next_url(endpoint)  # Get the next URL to resume from
        url = next_url if next_url else f"{self.base_url}{endpoint}/"
        all_data = []
        last_fetched_page = self.get_last_page(endpoint)  # Get the last page number fetched
        page_number = last_fetched_page - (last_fetched_page % save_after_pages)  # Adjust to last saved batch
        total_fetched = 0  # Track the total number of fetched items

        # Track time for progress reporting
        start_time = time.time()
        
        # Main loop to go through each page, fetch data and save it to a CSV file
        try:
            while url:
                # Handle rate limit
                if self.request_count >= self.max_requests_per_hour:
                    print(f"API limit reached. Pausing for 1 hour...")
                    time.sleep(3600)  # Sleep for 1 hour
                    self.request_count = 0  # Reset the request count after sleeping

                # This counts as 1 request: verified from CL API docs
                print(f"Fetching data from page {page_number}...")
                response = self.session.get(url, params=params)
                self.request_count += 1

                # Read the response code
                if response.status_code != 200:
                    print(f"Error: {response.status_code}, {response.text}")
                    break
                
                # Log progress if the function is expanded beyond a print statement
                self.log_progress(page_number) 

                # Read the response data 
                data = response.json()
                all_data.extend(data.get('results', []))
                
                # Update the total number of fetched items
                total_fetched += len(data.get('results', [])) 

                # Print progress
                print(f"Total items successfully fetched from page {page_number}: {total_fetched}")

                # Save data incrementally to csv
                if page_number % save_after_pages == 0:
                    # Process the data
                    all_data = self.process_data(all_data)
                    # Define filename using endpoint and page number
                    csv_filename = os.path.join(self.set_data_directory(endpoint), f"{endpoint}_page_{page_number}.csv")
                    # Save the data to a CSV file
                    self.save_to_csv(data=all_data, filename=csv_filename)
                    print(f"Data saved to {csv_filename}")
                    all_data = []  # Reset the data after saving to avoid memory issues
                
                # Save next URL and page number
                self.save_next_url_and_page(endpoint, data.get('next', None), page_number)
                
                # Handle pagination
                if 'next' in data and data['next']:
                    url = data['next']    
                    page_number += 1
                else:
                    break
        except KeyboardInterrupt:
            print("\nProcess interrupted. Here's a summary:")
            print(f"Last page URL: {url}")
            print(f"Last fetched page: {page_number}")
            print(f"Total records fetched: {total_fetched}")
            print("Don't worry, the progress has been saved. You can resume from the last page.")
        
        finally:
            print("Exiting gracefully. The last page and URL were logged.")
        total_time = time.time() - start_time
        print(f"Data fetched from {page_number - start_page + 1} pages in {total_time/60:.2f} minutes, total records fetched: {total_fetched}")
        return all_data

    # Function to process and flatten the data
    def process_data(self, data):
        processed_data = []  
        for item in data:
            # Flatten the dictionary and handle missing keys
            entry = {key: item.get(key, None) for key in item}  
            processed_data.append(entry)
        print(f"Total number of entries processed: {len(processed_data)}")
        return processed_data

    # Function to save the data to a CSV file
    def save_to_csv(self, data, filename):
        """
        Save the processed data to a CSV file.
        
        Args:
            data (list): The list of processed data (dictionaries).
            filename (str): The name of the CSV file to save the data.
        """
        if not data:
            print(f"No data to save for {filename}")
            return
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Write to CSV
        with open(filename, 'w', newline='') as csvfile: 
            fieldnames = data[0].keys()  # Get the column names from the first record
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()  # Write the header
            for item in data:
                writer.writerow(item)  # Write each row
        print(f"Data saved to {filename}")



class CLScraper(APIScraper):
    '''This class is used to scrape data from CourtListener
    Initially, it will serve to scrape positions, education, financial disclosures and docket data
    using CourtListener's search API. We will create two distinct methods to scrape docket data.
    '''
    def __init__(self, api_token, max_requests_per_hour=5000):
        """
        Initialize the CLScraper.

        Args:
            api_token (str): The API token for authentication.
            max_requests_per_hour (int, optional): Maximum number of requests allowed per hour. Defaults to 5000.
        """
        super().__init__(base_url="https://www.courtlistener.com/api/rest/v4/", api_token=api_token, max_requests_per_hour=max_requests_per_hour)

    def fetch_positions(self, **kwargs):
        """
        Fetch positions data from the CourtListener API.

        Args:
            **kwargs: Additional query parameters for the API request.

        Returns:
            list: A list of positions data.
        """
        return self.fetch_data(endpoint="positions", params=kwargs)

    
    def fetch_dockets(self, **kwargs):
        """
        Fetch dockets data from the CourtListener API.

        Args:
            **kwargs: Additional query parameters for the API request.

        Returns:
            list: A list of dockets data.
        """
        return self.fetch_data(endpoint="dockets", params=kwargs)