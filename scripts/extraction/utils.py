##############################################
# utils file for CourtListener scraper
# contains functions for logging errors,...
##############################################

import logging
import time

# Configure logging to write to a file
logging.basicConfig(filenname='error_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

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