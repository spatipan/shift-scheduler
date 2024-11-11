import json
import logging
import os
from datetime import datetime, timedelta, timezone
import streamlit as st

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
CONFIG_PATH = os.path.join(MASTER_PATH, 'config.json')

TIMEZONE = timezone(timedelta(hours= int(get_value_from_json(CONFIG_PATH, 'TIMEZONE_OFFSET'))))

# # Google apps
GOOGLE_SCOPES = get_value_from_json(CONFIG_PATH, 'GOOGLE_SCOPES')
SPREADSHEET_ID = get_value_from_json(CONFIG_PATH, 'SPREADSHEET_ID')
CALENDAR_ID = get_value_from_json(CONFIG_PATH, 'CALENDAR_ID')

# ## Google Sheet config
# SHEET_NAME = 'November 2024' # Default sheet name
# NAME_RANGE = 'E5'
# SHIFT_RANGE = 'C11:L42'
# EMPLOYEE_RANGE = 'A47:G67'
# FIXED_SHIFT_RANGE = 'C181:L212'
# OUTPUT_RANGE = 'C269:L299'
# HOLIDAYS_RANGE = 'B12:B42'
# DATE_RANGE = 'A12:A42'
# # SHIFT_MATRIX_RANGE = 'A210:J219'
# TOTAL_SHIFT_CONSTRAINT = 'B218:C240'
# SHIFT_PREFERENCE_RANGE = 'H218:J240'
# SHIFT_TYPE_PER_EMPLOYEE_RANGE = 'B217:F240'

SHEET_NAME = get_value_from_json(CONFIG_PATH, 'SHEET_NAME')
NAME_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['NAME_RANGE']
SHIFT_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['SHIFT_RANGE']
EMPLOYEE_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['EMPLOYEE_RANGE']
FIXED_SHIFT_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['FIXED_SHIFT_RANGE']
OUTPUT_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['OUTPUT_RANGE']
HOLIDAYS_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['HOLIDAYS_RANGE']
DATE_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['DATE_RANGE']
TOTAL_SHIFT_CONSTRAINT = get_value_from_json(CONFIG_PATH, 'RANGES')['TOTAL_SHIFT_CONSTRAINT']
SHIFT_PREFERENCE_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['SHIFT_PREFERENCE_RANGE']
SHIFT_TYPE_PER_EMPLOYEE_RANGE = get_value_from_json(CONFIG_PATH, 'RANGES')['SHIFT_TYPE_PER_EMPLOYEE_RANGE']



# Paths
GOOGLE_APP_PATH = os.path.join(MASTER_PATH, 'srcs/google_app')
SCHEDULER_APP_PATH = os.path.join(MASTER_PATH, 'srcs/scheduler_app')
SECRET_PATH = os.path.join(MASTER_PATH, 'secret.json')

#Secrets
CREDENTIALS = st.secrets['CRED']
TOKEN = st.secrets['TOKEN']


#Logging
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_TIME = datetime.now().strftime('%Y%m%d%H%M%S')
LOG_FILE_PATH = f'tmp/logging.log'

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