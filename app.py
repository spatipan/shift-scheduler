from modules.google_app import GoogleAppAuthenticator, CalendarApp
from modules.scheduler_app import Employee, Event, Schedule, ScheduleSolver, Shift, Task


# App configuration and logging

import logging
import os
from datetime import datetime
import config
import modules.google_app as google_app
# from modules.scheduler_app.schedule import Event, Task, Employee, Shift, Schedule
# from modules.scheduler_app.schedule_solver import ScheduleSolver, SchedulerConstraint, SchedulerConstraintGroup

class App:
    def __init__(self):
        self.logger = logging.getLogger(__class__.__name__)
        self.initialize()

        self.calendarApp = google_app.CalendarApp()
        self.sheetApp = google_app.GoogleSheetApp()
        self.schedulerApp = None
    
    def initialize(self):
        '''Initializes the app'''
        config.config_logging()
        self.logger.debug('App initialized')
    
    def start_google_apps(self):
        '''Authenticates the Google apps'''

        # authenticate user to google apps
        authenticator = google_app.GoogleAppAuthenticator(SCOPES = config.GOOGLE_SCOPES)
        credentials = authenticator.authenticate(
            credentials = config.CREDENTIALS,
            token = config.TOKEN,
        )

        # create calendar app
        self.calendarApp = google_app.CalendarApp(credentials)

        # create sheet app
        self.sheetApp = google_app.GoogleSheetApp(credentials)
        self.logger.debug('Google apps started')
        
   
    # get inputs
             
    def fetch_events(self, calendarId, start: datetime, end: datetime) -> list[Event]:
        '''Fetches events from google calendar, list as Event objects'''
        events = self.calendarApp.read(calendarId, start, end)
        return [Event.from_google_event(event) for event in events]


    # solve

    # analyze and visualize results
