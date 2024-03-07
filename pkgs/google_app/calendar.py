from datetime import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
from google.auth.external_account_authorized_user import Credentials as ExternalAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging




# Google calender app
class CalendarApp:
    def __init__(self, credentials: Credentials | ExternalAccountCredentials | None = None):
        self.credentials = credentials
        self.service = None
        self.logger = logging.getLogger(__class__.__name__)
        self.initialize()

    def initialize(self):
        '''Initialize google calendar service'''
        try:
            self.service = build('calendar', 'v3', credentials=self.credentials)
            self.logger.debug('Service initialized successfully')
        except Exception as e:
            print(f'Error initializing service: {e}')
            self.service = None
            self.logger.error(f'Error initializing service: {e}')
    
 
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
    
