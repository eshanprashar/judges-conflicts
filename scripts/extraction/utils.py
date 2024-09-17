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