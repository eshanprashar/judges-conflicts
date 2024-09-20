##############################################
# utils file for CourtListener scraper
# contains functions for finding the environment file, 
# logging errors,...
##############################################

from dotenv import load_dotenv
import os
import logging
import time

# Function to configure logging to write to a file
def configure_logging(log_dir, log_filename="error_log.txt"):
    """
    Configure logging to write to a file in the specified log directory.
    """
    os.makedirs(log_dir, exist_ok=True)  # Ensure log directory exists
    log_path = os.path.join(log_dir, log_filename)
    logging.basicConfig(filename=log_path, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def log_error_to_file(log_dir="logs"):
    """
    Decorator to log errors to a file in the specified log directory.
    
    Args:
        log_dir (str): Directory for saving error logs.
    
    Returns:
        decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_path = os.path.join(log_dir, "error_log.txt")
                with open(log_path, "a") as f:
                    f.write(f"Error in {func.__name__}: {str(e)}\n")
                print(f"An error occurred: {e}. Details logged to {log_path}")
                raise  # Re-raise the exception after logging
        return wrapper
    return decorator



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
    if not api_token:
        raise ValueError("API token not found. Please set the API_TOKEN in your .env file and save it in root directory.")
    else:
        return api_token