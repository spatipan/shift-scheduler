import config
import logging
from modules.google_app import GoogleAppAuthenticator, CalendarApp, GoogleSheetApp
from modules.scheduler_app.models.models import Event, Task, Employee, Shift, Schedule
from modules.scheduler_app.solver import ScheduleSolver, SchedulerConstraint, SchedulerConstraintGroup
from modules.scheduler_app.sheet_ui import SchedulerSheetUI


class SchedulerApp:
    def __init__(self):
        self.google_app_authenticator = GoogleAppAuthenticator(SCOPES = config.GOOGLE_SCOPES)
        credentials = self.google_app_authenticator.authenticate(
            credentials = config.CREDENTIALS,
            token = config.TOKEN,
        )
        self.calendar_app = CalendarApp(credentials) # init calendar app
        self.sheet_app = GoogleSheetApp(credentials) # init sheet app
        self.schedule = Schedule() # create a schedule
        self.schedule_solver = ScheduleSolver() # init solver app
        self.sheet_ui = SchedulerSheetUI(sheetApp=self.sheet_app, sheetId=config.SPREADSHEET_ID, sheetName=config.SHEET_NAME) # init sheet ui app

        self.logger = logging.getLogger(__class__.__name__)


    # [1] Fetch information from google apps (calendar, sheet)
        
    # [2] Update information into schedule (Employees, Shifts, Tasks, Holidays, Constraints)
    def fetch_information(self):
        self.schedule, self.schedule_solver = self.sheet_ui.extract_sheet_values()
        
    # [3] Call solver to solve the schedule
    def solve(self):
        self.schedule = self.schedule_solver.solve(schedule=self.schedule)
        
    # [4] Visualize the schedule (analyze and visualize results)
        
    # [5] Update the schedule into google apps (calendar, sheet)
        
    # [6] Save the schedule into a file
        
    
        
if __name__ == '__main__':
    app = SchedulerApp()
    
    # [1] Fetch information from google apps (calendar, sheet)
    app.sheet_ui.extract_sheet_values()



