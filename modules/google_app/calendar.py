from datetime import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
from google.auth.external_account_authorized_user import Credentials as ExternalAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest
import logging

# Google calender app
class CalendarApp:
    def __init__(self, credentials: dict | Credentials | ExternalAccountCredentials | None = None):
        self.credentials = credentials
        self.service = None
        self.logger = logging.getLogger(__class__.__name__)
        if credentials is not None:
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

        return events

    def create(self, calendarId: str, summary: str, start: datetime, end: datetime, description: str | None = None, location: str | None = None):
        assert start < end, 'Start time must be before end time'
        assert self.service is not None, 'Service not initialized'

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end.isoformat(),
                'timeZone': 'UTC',
            },
            'extendedProperties': {
                'shared': {  # Or 'private' if you don't want other users to see it
                    'generatedBy': 'Shift Scheduler'
                }
            }
        }

        try:
            created_event = self.service.events().insert(calendarId=calendarId, body=event).execute()
            self.logger.info(f'Event created: {created_event["summary"]}')
            return created_event
        except HttpError as error:
            self.logger.error(f'An error occurred: {error}')
            return None

    def update(self, calendarId: str, eventId: str, summary: str | None = None, start: datetime | None = None, end: datetime | None = None, description: str | None = None, location: str | None = None):
        assert self.service is not None, 'Service not initialized'

        try:
            event = self.service.events().get(calendarId=calendarId, eventId=eventId).execute()

            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if location:
                event['location'] = location
            if start:
                event['start']['dateTime'] = start.isoformat()
                event['start']['timeZone'] = 'UTC'
            if end:
                event['end']['dateTime'] = end.isoformat()
                event['end']['timeZone'] = 'UTC'

            if start and end:
                assert datetime.fromisoformat(event['start']['dateTime'].replace('Z','')) < datetime.fromisoformat(event['end']['dateTime'].replace('Z','')), 'Start time must be before end time'

            updated_event = self.service.events().update(calendarId=calendarId, eventId=eventId, body=event).execute()
            self.logger.info(f'Event updated: {updated_event["summary"]}')
            return updated_event
        except HttpError as error:
            self.logger.error(f'An error occurred: {error}')
            return None

    def delete(self, calendarId: str, eventId: str):
        assert self.service is not None, 'Service not initialized'

        try:
            self.service.events().delete(calendarId=calendarId, eventId=eventId).execute()
            self.logger.info(f'Event deleted: {eventId}')
            return True
        except HttpError as error:
            self.logger.error(f'An error occurred: {error}')
            return False


    def batch_create(self, calendarId: str, events_data: list):
        """Creates multiple events in a batch."""
        assert self.service is not None, 'Service not initialized'

        batch = BatchHttpRequest()
        created_events = []

        def callback(request_id, response, exception):
            if exception is None:
                created_events.append(response)
                self.logger.info(f'Event created: {response["summary"]}')
            else:
                self.logger.error(f'Error creating event: {exception}')

        for event_data in events_data:
            event = {
                'summary': event_data['summary'],
                'location': event_data.get('location'),
                'description': event_data.get('description'),
                'start': {
                    'dateTime': event_data['start'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end'].isoformat(),
                    'timeZone': 'UTC',
                },
                'extendedProperties': {
                    'shared': {
                        'generatedBy': 'Shift Scheduler'
                    }
                }
            }
            batch.add(self.service.events().insert(calendarId=calendarId, body=event), callback=callback)

        batch.execute()
        return created_events
    

    def batch_delete(self, calendarId: str, event_ids: list):
        """Deletes multiple events in a batch."""
        assert self.service is not None, 'Service not initialized'

        batch = BatchHttpRequest()
        deleted_event_ids = []

        def callback(request_id, response, exception):
            if exception is None:
                deleted_event_ids.append(request_id)
                self.logger.info(f'Event deleted: {request_id}')
            else:
                self.logger.error(f'Error deleting event: {exception}')

        for event_id in event_ids:
            batch.add(self.service.events().delete(calendarId=calendarId, eventId=event_id), request_id=event_id, callback=callback)

        batch.execute()
        return deleted_event_ids

# Example usage:
# event_ids_to_delete = ['event_id_1', 'event_id_2', 'event_id_3']
# calendar_app.batch_delete(calendar_id, event_ids_to_delete)