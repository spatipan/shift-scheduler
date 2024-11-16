
# from pkgs.google_app import GoogleAppAuthenticator, CalendarApp
# from pkgs.scheduler_app import *
from modules.scheduler_app.models.models import Event, Task, Employee, Shift, Schedule
from modules.scheduler_app.solver import ScheduleSolver, SchedulerConstraint, SchedulerConstraintGroup
from modules.scheduler_app import SchedulerApp
from modules.google_app import GoogleAppAuthenticator, CalendarApp, GoogleSheetApp

from datetime import datetime
import config
import logging
# from app import App

def main_test() -> None:
    
    config.config_logging()

    app = SchedulerApp()
    app.fetch_information()
    events = app.calendar_app.events

    app.solve()
    app.schedule.summary()
    # app.visualize()
    app.update_information()

import functions_framework

@functions_framework.http
def main(request):
    try:
        # data = request.get_json()
        # logging.info(f'Data received: {data}')
        main_test()
        print('Function triggered')
        return 'Success', 200
    except Exception as e:
        # logging.error(f'Error: {e}')
        print(f'Error: {e}')
        return 'Error', 500

# import function_framework
# from main import main
# import logging

# @function_framework.http
# def handler(request):
#     logging.info('Function triggered')
    
#     try:
#         data = request.get_json()
#         logging.info(f'Data received: {data}')
#         main()
#         return 'Success', 200
#     except Exception as e:
#         logging.error(f'Error: {e}')
#         return 'Error', 500
    

if __name__ == '__main__':
    main_test()
    

    

