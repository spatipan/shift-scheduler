from modules.google_app.calendar import CalendarApp
from datetime import datetime
from modules.scheduler_app.models.models import Event
import logging

class SchedulerCalendarUI:
    '''Calendar UI for the scheduler app.
    use Google Calendar as UI for the scheduler app
    and store the data in the Google Calendar
    '''
    def __init__(self, calendarApp: CalendarApp, calendarId: str):
        self.calendarApp = calendarApp
        self.calendarId = calendarId
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.debug(f'SchedulerCalendarUI initialized - calendarId: {calendarId}')

    # fetch all events from the given calendar
    def fetch_events(self, start: datetime, end: datetime) -> list[Event]:
        '''Fetches events from google calendar, list as Event objects'''
        events = self.calendarApp.read(self.calendarId, start, end)
        return [Event.from_google_event(event) for event in events]

