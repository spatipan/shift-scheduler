
# from pkgs.google_app import GoogleAppAuthenticator, CalendarApp
# from pkgs.scheduler_app import *
from modules.scheduler_app.models.models import Event, Task, Employee, Shift, Schedule
from modules.scheduler_app.solver import ScheduleSolver, SchedulerConstraint, SchedulerConstraintGroup
from modules.scheduler_app import SchedulerApp
from modules.google_app import GoogleAppAuthenticator, CalendarApp, GoogleSheetApp

from datetime import datetime
import config
import logging
from app import App

def main() -> None:
    
    config.config_logging()

    # credentials = config.get_value_from_json(config.SECRET_PATH, 'credentials', '')
    # authenticator = GoogleAppAuthenticator(SCOPES = config.GOOGLE_SCOPES)
    # credentials = authenticator.authenticate(
    #     credentials = config.CREDENTIALS,
    #     token = config.TOKEN,
    # )


    # app = GoogleSheetApp(credentials)

    # values = app.read(spreadsheetId=config.SPREADSHEET_ID, sheetName=config.SHEET_NAME, range='A1:Z100')

    # print(values)

    app = SchedulerApp()
    app.fetch_information()
    app.solve()

    # shifts = app.sheet_ui.schedule.shifts
    
    # for shift in shifts:
        # print(f'Title: {shift.title}, Start: {shift.start}, End: {shift.end}, Duration: {shift.duration}, Employees: {shift.employees}')
    # app.sheet_ui.schedule.summary()

    # app.sheet_ui.schedule.visualize()
 





if __name__ == '__main__':
    main()
    

    

