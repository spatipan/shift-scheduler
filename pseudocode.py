from datetime import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import logging
# Event object

class Event:
    def __init__(self, start: datetime, end: datetime, title: str, users: list, description: str = ''):
        assert start < end, 'Start time must be before end time'
        self.start = start
        self.end = end
        self.title = title
        self.user = users

    def __repr__(self):
        return f'{self.title} starts at {self.start} and ends at {self.end}'
    
    def duration(self):
        return (self.end - self.start).seconds
    
    def overlap(self, other: 'Event'):
        return self.start <= other.end and self.end >= other.start
    
    def contains(self, other: 'Event'): 
        return self.start <= other.start and self.end >= other.end
    
# Task object - inherits from Event

class Task(Event):
    def __init__(self, start: datetime, end: datetime, title: str, users: list, description: str = ''):
        super().__init__(start, end, title, users, description = description)

    def __repr__(self):
        return f'{self.title} starts at {self.start} and ends at {self.end}'
    
    # skill required for task
    # required number of people for task


# shift object - inherits from Event

class Shift(Event):
    def __init__(self, start: datetime, end: datetime, shift_type: str, title: str = '', required_assignees: int = 1, assignned_staffs: list = [], description: str = ''):
        super().__init__(start, end, title, users = assignned_staffs, description = description)
        self.shift_type = shift_type
        self.required_skills = []
        self.required_assignees = required_assignees
        if title == '':
            self.title = f'{shift_type.capitalize()} shift'

    def __repr__(self):
        return f'{self.title} shift starts at {self.start} and ends at {self.end}'
    
    # skill required for shift
    # required number of people for shift
    # shift type (day, night, etc)
  

# Employee object
    
class Employee:
    def __init__(self, first_name: str, last_name: str, abbreviation: str = '', skills: list = []):
        self.first_name = first_name
        self.last_name = last_name

        if abbreviation == '':
            self.abbreviation = first_name[0].upper() + last_name[0].upper()
        self.abbreviation = abbreviation
        self.tasks = []
        self.shifts = []
        self.skills = skills
        

# Schedule object
        
class Schedule:
    def __init__(self, title: str, 
                 description: str = '', 
                 employees: list = [], 
                 shifts: list = [], 
                 tasks: list = []):
        self.title = title
        self.description = description
        self.employees = employees
        self.shifts = shifts
        self.tasks = tasks
        self.events = shifts + tasks

        #check unique employee abbreviations
    

# Constraint object - constraint, status
class SchedulerConstraint:
    def __init__(self, model, constraint, group: str, status: str, *args, **kwargs):
        self.model = model
        self.constraint = constraint
        self.group = group
        self.status = status
        self.args = args
        self.kwargs = kwargs


# Constraint group object - constraints, status

class SchedulerConstraintGroup:
    def __init__(self, title: str, constraints: list, status: str):
        self.title = title
        self.constraints = constraints
        self.status = status
    
# Schedule solver
class ScheduleSolver:
    def __init__(self, schedule: Schedule):
        self.schedule = schedule
        self.model = None # Initialize model - gurobi, ortools, etc
        self.constraints = []
        self.constraint_groups = []
        self.status = '' # unsolved, infeasible, feasiblem optimal
        self.solutions = []
    
    def add_constraint(self, constraint: SchedulerConstraint):
        self.constraints.append(constraint)
        # then  solve constraints group by group

    def visualize(self):
        '''Visualize schedule using matplotlib, plotly, etc.'''
        pass
        # visualize schedule

    def check_feasibility(self):
        pass
        # solve only constraint group by group
    
    def solve(self):
        pass
    
    def get_solution(self):
        pass
    
    def get_status(self):
        pass
    

# Google calender app
class CalendarApp:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = None

    def initialize(self):
        pass
        # initialize service
    
 
    def read(self, calendarId: str, start: datetime, end: datetime):
        assert start < end, 'Start time must be before end time'
        assert self.service is not None, 'Service not initialized'

        self.calendarId = calendarId

        # Call the Calendar API
        events_result = self.service.events().list( 
            calendarId=calendarId, 
            timeMin=start.isoformat() + 'Z', 
            timeMax=end.isoformat() + 'Z', 
            singleEvents=True, 
            orderBy='startTime',
            ).execute()
        
        events = events_result.get('items', [])
        self.events = events

        if not events:
            print(f'No events found between {start} and {end}')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

        return events



        # read events from google calendar
    

# Google Sheet app - as UI for schedule
class GoogleSheetApp:
    def __init__(self, credentials: Credentials | None = None):
        self.credentials = credentials
        self.service = None
        self.service = self.initialize()
    
    def initialize(self):
        pass
        # initialize service
        
        

# GoogleCloud app
class GoogleAppAuthenticator:
    def __init__(self, SCOPES: list = ['https://www.googleapis.com/auth/calendar.readonly', 
                                      'https://www.googleapis.com/auth/spreadsheets.readonly']):
        self.credentials = None
        self.token = None
        self.authenticated = False
        self.service = None
        self.SCOPES = SCOPES

    def authenticate(self, path: str = 'credentials/',
                    credential_filename: str = 'credentials.json',
                    token_filename: str = 'token.json'):
        assert os.path.exists(path + credential_filename), f'Credentials file not found at {path + credential_filename}'
        assert os.path.exists(path), f'Path not found at {path}'

        if self.authenticated:
            print('User already authenticated')
            return self.credentials 

        try:
            if os.path.exists(path + token_filename):
                creds = Credentials.from_authorized_user_file(token_filename, self.SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        path + credential_filename, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    # Save the credentials for the next run
                with open(path + token_filename, "w") as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.authenticated = True
        except Exception as e:
            print(f'Error authenticating user: {e}')

        return self.credentials




# Scheduler app
class SchedulerApp:
    def __init__(self, schedule: Schedule):
        self.schedule = schedule
        
        self.status = None # error, unsolved, infeasible, feasible, optimal

        self.scopes = ['https://www.googleapis.com/auth/calendar.readonly', 
                       'https://www.googleapis.com/auth/spreadsheets.readonly']
        self.solver = ScheduleSolver(schedule)
        self.calendar = CalendarApp(self.scopes)
        self.sheet = GoogleSheetApp(self.scopes)

        self.logger = logging.getLogger('scheduler_app')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())
        self.logger.info('Scheduler app initialized')


# Firebase app - for user authentication and data storage

    