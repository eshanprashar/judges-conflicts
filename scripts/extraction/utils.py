##############################################
# utils file for CourtListener scraper
# contains functions for finding the environment file, 
# logging errors,...
##############################################

from dotenv import load_dotenv
import os
import logging
import time

# Configure logging to write to a file
logging.basicConfig(filename='error_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def log_error_to_file(func):
    '''Decorator that wraps the passed function and logs any errors to a file
    '''
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f'Error in function {func.__name__}: {e}', exc_info=True)
            raise e
    return wrapper

def find_env_file():
    '''Recursively searches for a .env file starting from the current directory
    Returns the full path if found; otherwise None
    '''
    current_dir = os.getcwd()
    while current_dir != os.path.dirname(current_dir): # checks if we are at root directory
        for file in os.listdir(current_dir):
            if file.endswith('.env'):
                env_path = os.path.join(current_dir, file)
                return env_path
        current_dir = os.path.dirname(current_dir) # move up one directory
    return None

def get_api_token():
    '''Loads the API token from the .env file
    Retuns the API token
    '''
    # Load api_token from .env file
    env_file_path = find_env_file()
    if env_file_path:
        print(f"Found .env file at {env_file_path}")
        load_dotenv(env_file_path)
    else:
        raise FileNotFoundError("No .env file found. Please create one and save it in the root directory.")

    # Access envionment variables
    api_token = os.getenv('API_TOKEN')
    if not API_TOKEN:
        raise ValueError("API token not found. Please set the API_TOKEN in your .env file and save it in root directory.")
    else:
        return api_token