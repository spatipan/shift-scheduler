from modules.google_app import GoogleAppAuthenticator, CalendarApp, GoogleSheetApp
from datetime import datetime, timedelta
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
                    schedule.add_task(task)
                self.logger.debug(f'Extracted task: {task} for employee: {r", ".join([employee.display_name for employee in task.user])}')          

        # schedule.employees = employee_list
        # schedule.tasks = [task for employee in employee_list for task in employee.tasks]
            
        return schedule
            
    def read_generated_events(self, start: datetime, end: datetime) -> list[Event]:
        '''Fetches generated events from Shift Scheduler, list as Event objects'''
        events = self.calendarApp.read(self.calendarId, start, end)
        generated_events = [
            event for event in events
            if event.get('extendedProperties', {}).get('shared', {}).get('generatedBy') == 'Shift Scheduler'
        ]
        return generated_events


    def create_event(self, summary: str, start: datetime, end: datetime, description: str | None = None, location: str | None = None):
        assert start < end, 'Start time must be before end time'
        
        try:
            self.calendarApp.create(
                self.calendarId,
                summary=summary,
                start=start,
                end=end,
                description=description,
            )

            self.logger.info(f'Event created: {summary} - {start} - {end}')
        except Exception as e:
            self.logger.error(f'Error creating event: {e}')
            raise e
        
    def create_events(self, events, batch = True, batch_size = 100):
        assert events is not None, 'Events is empty'
        if batch:
            for i in range(0, len(events), batch_size):
                batch_events = events[i:i+batch_size]
                self.calendarApp.batch_create(self.calendarId, batch_events)
            self.logger.info(f"Batch {len(events)} events created")
        else:
            for event in events:
                self.create_event(
                    summary=event.summary,
                    start=event.start,
                    end=event.end,
                    description=event.description,
                )
            


    # delete all events that is tagged with 'extendedProperties': {'shared': {'generatedBy': 'Shift Scheduler'}
    def delete_generated_events(self, start: datetime, end: datetime, batch = False, batch_size = 100):
        assert start < end, 'Start time must be before end time'
        assert start is not None, 'Start time is empty'
        assert end is not None, 'End time is empty'
        events = self.read_generated_events(start, end)

        # if batch: # For efficiency
        #     for i in range(0, len(events), batch_size):
        #         batch_events = events[i:i+batch_size]
        #         event_ids = [event['id'] for event in batch_events] # type: ignore
        #         self.calendarApp.batch_delete(self.calendarId, event_ids)
        #     self.logger.info(f"Batch {len(events)} events deleted")
        # else:   
        for event in events:
            self.calendarApp.delete(self.calendarId, event['id'])  # type: ignore
            self.logger.info(f"Event deleted: {event['summary']}") # type: ignore

    def update_calendar(self, schedule: Schedule, batch = True, batch_size = 100):
        '''Update the calendar with the schedule'''
        
        # if batch: # Batch create for efficiency
        #     events = []
        #     for shift in schedule.shifts:
        #         assigned_employees = " ".join([employee.abbreviation for employee in shift.employees])
        #         shift_type = shift.type
        #         title = f"{str.upper(assigned_employees)} ({str.upper(shift_type)})"
        #         start = shift.start
        #         end = shift.end
        #         events.append({
        #             'summary': title,
        #             'start': start,
        #             'end': end,
        #         })
        #     self.create_events(events, batch, batch_size)
        # else:
        
        for date in schedule.dates:
            shifts_on_date = schedule.get_shifts_by_date(date)
            for shifts in shifts_on_date:
                mc = [shift.employees[0] for shift in shifts if shift.type == "mc"][0] #type: ignore
                s1 = [shift.employees[0] for shift in shifts if shift.type == "service1"][0] #type: ignore
                s2 = [shift.employees[0] for shift in shifts if shift.type == "service2"][0] #type: ignore
                s1p = [shift.employees[0] for shift in shifts if shift.type == "service1+"][0] #type: ignore
                s2p = [shift.employees[0] for shift in shifts if shift.type == "service2+"][0] #type: ignore
                ems = [shift.employees[0] for shift in shifts if shift.type == "ems"][0] #type: ignore
                observe = [shift.employees[0] for shift in shifts if shift.type == "observe"][0] #type: ignore
                amd = [shift.employees[0] for shift in shifts if shift.type == "amd"][0] #type: ignore
                avd = [shift.employees[0] for shift in shifts if shift.type == "avd"][0] #type: ignore

                event1_title = f''
                
        

           
            title = f"{str.upper(assigned_employees)} ({str.upper(shift_type)})"
            start = shift.start
            end = shift.end
            self.create_event(
                summary=title,
                start=start,
                end=end,
            )

        
if __name__ == '__main__':

    app_auth = GoogleAppAuthenticator(
        credentials_path=config.CREDS_PATH,
        token_path=config.TOKEN_PATH,
        scopes=config.GOOGLE_SCOPES,
    )
    credentials = app_auth.authenticate()
    calendar_app = CalendarApp(credentials=credentials)

    

    calendar_ui = SchedulerCalendarUI(calendarApp=calendar_app, calendarId=config.CALENDAR_ID)

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)

    print("Auth successful")

    # read events
    # events = calendar_ui.fetch_events(start_date, end_date)
    # for event in events:
    #     print(event)

    # generate an event
    calendar_ui.create_event(
        summary='Test Event',
        start= start_date,
        end= start_date + timedelta(hours=1),
        description='This is a test event',
    )

    print(f'create an event successfully')

    # read generated events
    generated_events = calendar_ui.read_generated_events(start_date, end_date)
    print(f"{len(generated_events)} is/are found")
    for event in generated_events:
        print(f"   - {event['summary']}") # type: ignore

    # delete tagged events
    calendar_ui.delete_generated_events(start_date, end_date)
    print(f"{len(generated_events)} tagged event(s) deleted")





# event class
# {'kind': 'calendar#event', 
#  'etag': '"3484773719664382"', 
#  'id': '8s3pboi5iankdr3656gi50m8qg', 
#  'status': 'confirmed', 
#  'htmlLink': 'https://www.google.com/calendar/event?eid=OHMzcGJvaTVpYW5rZHIzNjU2Z2k1MG04cWcgZW0uY211LnRlYWNoZXJAbQ', 
#  'created': '2025-03-19T12:20:59.000Z', 
#  'updated': '2025-03-19T12:20:59.832Z', 
#  'summary': 'Test Event', 
#  'description': 'This is a test event', 
#  'creator': {'email': 'patipan120897@gmail.com'}, 
#  'organizer': {'email': 'em.cmu.teacher@gmail.com', 
#                'self': True}, 
# 'start': {
#     'dateTime': '2024-01-01T07:00:00+07:00', 'timeZone': 'UTC'}, 
#     'end': {'dateTime': '2024-01-01T08:00:00+07:00', 'timeZone': 'UTC'}, 
#     'iCalUID': '8s3pboi5iankdr3656gi50m8qg@google.com', 
#     'sequence': 0, 
#     'extendedProperties': {
#         'shared': {
#             'generatedBy': 'Shift Scheduler'}}, 
# 'reminders': {'useDefault': True}, 
# 'eventType': 'default'}

