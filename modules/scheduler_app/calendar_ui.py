from modules.google_app.calendar import CalendarApp
from datetime import datetime
from modules.scheduler_app.models.models import Event, Task, Employee, Shift, Schedule
import logging
import re
from datetime import datetime, timezone
import config

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
        self.logger.debug(f'Sample event: {events[0]}')
        return [Event.from_google_event(event) for event in events]
    
    def extract_employee_tasks(self, schedule: Schedule):
        '''Extracts tasks from the calendar events'''
        assert schedule is not None, 'Schedule is empty'
        assert schedule.start is not None, 'Schedule start date is empty'
        assert schedule.end is not None, 'Schedule end date is empty'
        events = self.fetch_events(schedule.start, schedule.end)
        employee_list = schedule.employees
        employee_abbreviations = [employee.abbreviation for employee in employee_list]
        for event in events:
            # use regex to extract employee abbreviation from event title
            pattern = r'|'.join(employee_abbreviations)
            matches = re.findall(pattern, event.title)
            if matches:
                task = Task.from_event(event)
                for employee_abbreviation in matches:
                    employee = [employee for employee in employee_list if employee.abbreviation == employee_abbreviation][0]
                    employee.add_task(task)
                    task.user.append(employee)
                    # self.logger.debug(f'found: {task} for employee: {employee.display_name}')
                self.logger.debug(f'Extracted task: {task} for employee: {r", ".join([employee.display_name for employee in task.user])}')          

        schedule.employees = employee_list
        schedule.tasks = [task for employee in employee_list for task in employee.tasks]
            
        return schedule
            

