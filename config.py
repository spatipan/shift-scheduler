import json
import logging
import os
from datetime import datetime, timedelta, timezone


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
    

TIMEZONE = timezone(timedelta(hours=7))

MASTER_PATH = os.path.dirname(os.path.abspath(__file__))

#Logging
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_TIME = datetime.now().strftime('%Y%m%d%H%M%S')
LOG_FILE_PATH = f'tmp/logging.log'

# Google apps
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar', 
                'https://www.googleapis.com/auth/spreadsheets',
                ]
SPREADSHEET_ID = '1wHNERHZUxl8mI7xOPtWsvRBHxw9r_ohFoi7BWET_YdU'
CALENDAR_ID = 'em.cmu.teacher@gmail.com'

## Google Sheet config
SHEET_NAME = 'May 2024' # Default sheet name
NAME_RANGE = 'E5'
SHIFT_RANGE = 'C11:M42'
EMPLOYEE_RANGE = 'A47:G67'
FIXED_SHIFT_RANGE = 'C181:M212'
OUTPUT_RANGE = 'C269:M299'
HOLIDAYS_RANGE = 'B12:B42'
DATE_RANGE = 'A12:A42'
# SHIFT_MATRIX_RANGE = 'A210:J219'
TOTAL_SHIFT_CONSTRAINT = 'B219:C240'
SHIFT_PREFERENCE_RANGE = 'H219:J240'


# Paths
GOOGLE_APP_PATH = os.path.join(MASTER_PATH, 'srcs/google_app')
SCHEDULER_APP_PATH = os.path.join(MASTER_PATH, 'srcs/scheduler_app')
SECRET_PATH = os.path.join(MASTER_PATH, 'secret.json')

#Secrets
CREDENTIALS = get_value_from_json(SECRET_PATH, 'credentials')
TOKEN = get_value_from_json(SECRET_PATH, 'token')


def config_logging():
    logging.basicConfig(level=logging.DEBUG,
                    format = '%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
                    datefmt = LOG_DATE_FORMAT,
                    filename = LOG_FILE_PATH,
                    filemode = 'w',
                    force = True)
    # print(f'Logging to {LOG_FILE_PATH}')
    logger = logging.getLogger(__name__)
    logger.debug(f'Logging to {LOG_FILE_PATH}')


if __name__ == '__main__':
    config_logging()
    
    logger = logging.getLogger(__name__)
    logger.debug('main() started')
    print('main() started')