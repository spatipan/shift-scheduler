import json
import logging
import os
from datetime import datetime


def get_value_from_json(path: str, key: str, subkey: str = ''):
    try:
        with open(path) as f:
            data = json.load(f)
            logging.debug(f'Value read from {path}')
            if subkey == '':
                return data[key]
            else:
                return data[key][subkey]
    
    except Exception as e:
        print(f'Error reading {key} from {path}: {e}')
        logging.error(f'Error reading {key} from {path}: {e}')
        return {}
    

MASTER_PATH = os.path.dirname(os.path.abspath(__file__))

#Logging
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_TIME = datetime.now().strftime('%Y%m%d%H%M%S')
LOG_FILE_PATH = f'version4/tmp/logging.log'

# Google app 
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 
                'https://www.googleapis.com/auth/spreadsheets.readonly']

# Paths
GOOGLE_APP_PATH = os.path.join(MASTER_PATH, 'srcs/google_app')
SCHEDULER_APP_PATH = os.path.join(MASTER_PATH, 'srcs/scheduler_app')
SECRET_PATH = os.path.join(MASTER_PATH, 'secret.json')

#Secrets
CREDENTIALS = get_value_from_json(SECRET_PATH, 'credentials')
TOKEN = get_value_from_json(SECRET_PATH, 'token')


def config_logging():
    logging.basicConfig(level=logging.DEBUG,
                    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt = LOG_DATE_FORMAT,
                    filename = LOG_FILE_PATH,
                    filemode = 'a',
                    force = True)
    print(f'Logging to {LOG_FILE_PATH}')
    logger = logging.getLogger(__name__)
    logger.debug('log_config() started')


if __name__ == '__main__':
    config_logging()
    
    logger = logging.getLogger(__name__)
    logger.debug('main() started')
    print('main() started')