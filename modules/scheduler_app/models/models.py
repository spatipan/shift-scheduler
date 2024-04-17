from datetime import datetime, timedelta
import logging
import plotly.express as px
from plotly.colors import n_colors
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import config

class Event:
    def __init__(self, start: datetime, end: datetime, title: str, users: list = [], description: str = ''):
        assert start < end, 'Start time must be before end time'
        self.start = start
        self.end = end
        self.title = title
        self.user = users
    
    @property
    def date(self):
        return self.start.date()

    def __repr__(self):
        start_text = self.start.strftime("%Y-%m-%d %H:%M:%S")
        end_text = self.end.strftime("%Y-%m-%d %H:%M:%S")
        return f'[{start_text} -> {end_text}] - {self.title}'
    
    def duration(self):
        return (self.end - self.start).seconds
    
    def overlap(self, other: 'Event'):
        assert isinstance(other, Event), 'Other must be an Event object'
        # assert datetime start and end is offset aware
        assert self.start.tzinfo is not None and self.end.tzinfo is not None, f'Start and end time must be offset aware {self.title}'
        assert other.start.tzinfo is not None and other.end.tzinfo is not None, f'Start and end time must be offset aware {other.title}'
        return self.start <= other.end and self.end >= other.start
    
    def contains(self, other: 'Event'): 
        return self.start <= other.start and self.end >= other.end
    
    @staticmethod
    def from_google_event(google_event: dict) -> 'Event':
        start = google_event["start"].get("dateTime", google_event["start"].get("date"))
        start = datetime.fromisoformat(start)
        end = google_event["end"].get("dateTime", google_event["end"].get("date"))
        end = datetime.fromisoformat(end)
        title = google_event["summary"]
        return Event(start=start, end=end, title=title)
    

class Task(Event):
    def __init__(self, start: datetime, end: datetime, title: str, users: list = [], description: str = ''):
        super().__init__(start, end, title, users = users.copy(), description = description)

    def __repr__(self):
        return f'{self.title} starts at {self.start} and ends at {self.end}'
    
    @staticmethod
    def from_event(event: Event) -> 'Task':
        start = event.start.astimezone(tz=config.TIMEZONE)
        end = event.end.astimezone(tz=config.TIMEZONE)
        return Task(start = start, end = end, title = event.title, users = event.user.copy(), description = '')
    
    

class Shift(Event):
    def __init__(self, start: datetime, end: datetime, type: str, title: str = '', required_assignees: tuple = (1,1), assignned_employees: list = [], description: str = ''):
        super().__init__(start, end, title, users = assignned_employees.copy(), description = description)
        self.type = type
        self.required_skills = []
        self.required_assignees = required_assignees # (min, max)
        self.employees = assignned_employees.copy() if len(assignned_employees) > 0 else []
        if title == '':
            self.title = f'{type.capitalize()} shift'

    @property
    def date(self):
        return self.start.date()
    
    @property
    def min_employees(self):
        return self.required_assignees[0]
    
    @property
    def max_employees(self):
        return self.required_assignees[1]

    def __repr__(self):
        return f'{self.title} shift starts at {self.start} and ends at {self.end}'
    
    def add_employee(self, employee):
        if employee in self.employees:
            raise Exception('Employee already exists')
        self.employees.append(employee)
    
    # @staticmethod
    # def from_dict(shift: dict) -> 'Shift':
    #     return Shift(
    #         start = datetime.fromisoformat(shift['start']),
    #         end = datetime.fromisoformat(shift['end']),
    #         shift_type = shift['shift_type'],
    #         title = shift['title'],
    #         required_assignees = int(shift['required_assignees']),

    #         description = shift['description']
    #     )
    

class Employee:
    def __init__(self, first_name: str, last_name: str, abbreviation: str = '', skills: list = [], active: bool = True):
        self.first_name = first_name
        self.last_name = last_name

        if abbreviation == '':
            self.abbreviation = first_name[0].upper() + last_name[0].upper()
        self.abbreviation = abbreviation
        self.tasks = []
        self.shifts = []
        self.skills = skills
        self.active = active

    @property
    def display_name(self):
        return f'{self.first_name} {self.last_name} ({self.abbreviation})'

    def __repr__(self):
        return f'[Employee] - {self.first_name} {self.last_name} ({self.abbreviation})'

    @staticmethod
    def from_dict(employee: dict) -> 'Employee':
        # print(f'Creating employee from dict: {employee}')
        return Employee(
            first_name = employee['first_name'],
            last_name = employee['last_name'],
            abbreviation = employee['abbreviation'],
            skills = [employee['role']], # TODO: change to skills
            active = employee['active'] == 'TRUE' or employee['active'] == 'true'
        )
    
    def add_task(self, task: Task):
        if task in self.tasks:
            raise Exception('Task already exists')
        self.tasks.append(task)

        
    def add_shift(self, shift: Shift):
        if shift in self.shifts:
            raise Exception('Shift already exists')
        self.shifts.append(shift)

    def is_available(self, event: Event):
        for shift in self.shifts:
            if shift.overlap(event):
                return False
        for task in self.tasks:
            if task.overlap(event):
                return False
        return True

class Schedule:
    def __init__(self, 
                title: str = 'Untitled Schedule', 
                start: datetime | None = None,
                end: datetime | None = None,
                description: str = '', 
                employees: list[Employee] = [], 
                shifts: list[Shift] = [], 
                tasks: list[Task] = []):
        self.title = title
        self.start = start
        self.end = end
        self.description = description
        self.employees = employees
        self.shifts = shifts
        self.tasks = tasks
        self.events = shifts + tasks

        self.holidays = []

        self.logger = logging.getLogger(__class__.__name__)


    @property
    def dates(self) -> list[datetime]:
        assert self.start is not None and self.end is not None, 'Start and end date must be set'
        return [self.start + timedelta(days=x) for x in range(self.duration.days + 1)]
    
    @property
    def duration(self) -> timedelta:
        assert self.start is not None and self.end is not None, 'Start and end date must be set'
        return self.end - self.start
    
    @property
    def days(self) -> list:
        return [date.date() for date in self.dates]
    
    @property
    def holiday_dates(self) -> list:
        return [holiday.date() for holiday in self.holidays]

    @property
    def roles(self) -> set:
        return(set([employee.skills for employee in self.employees]))

    @property
    def shift_types(self) -> set:
        return set([shift.type for shift in self.shifts])
    
    @property
    def num_shifts(self) -> int:
        return len(self.shifts)
    
    @property
    def num_employees(self) -> int:
        return len(self.employees)
    
    @property
    def num_holidays(self) -> int:
        return len(self.holidays)
    
    @property
    def num_days(self) -> int:
        return self.duration.days + 1

    def set_date_range(self, start: datetime, end: datetime):
        '''Set the date range for the schedule'''
        self.start = start
        self.end = end

    def add_employee(self, employee: Employee):
        '''Add employee to the schedule'''
        self.employees.append(employee)

    def add_shift(self, shift: Shift):
        '''Add shift to the schedule'''
        self.shifts.append(shift)
        self.events.append(shift)

    def add_task(self, task: Task):
        '''Add task to the schedule'''
        self.tasks.append(task)
        self.events.append(task)

    def remove_employee(self, employee: Employee):
        self.employees.remove(employee)

    def remove_shift(self, shift: Shift):
        self.shifts.remove(shift)
        self.events.remove(shift)

    def remove_task(self, task: Task):
        self.tasks.remove(task)
        self.events.remove(task)

    def list_employees(self):
        return self.employees
    
    def list_shifts(self):
        return self.shifts
    
    def list_tasks(self):
        return self.tasks
    
    def assign_shift(self, shift: Shift, employee: Employee):
        '''Assign shift to an employee'''
        shift.add_employee(employee)
        employee.add_shift(shift)
        self.logger.debug(f'Assigned shift {shift.title} to {employee.first_name} {employee.last_name}')
    
    def get_shifts_by_date(self, date: datetime):
        '''Get shifts by date'''
        # print(f'Getting shifts for {date.date()}', [shift for shift in self.shifts if shift.start.date() == date.date()])
        return [shift for shift in self.shifts if shift.start.date() == date.date()]
    
    def add_holiday(self, date: datetime) -> None:
        # Check if date is in dates 
        if date not in self.dates:
            raise ValueError('Date is not in schedule')
        # Check if date is already a holiday
        if date in self.holidays:
            pass
        else:
            self.holidays.append(date)
   
    # function: visualize schedule as a table
    def summary(self):
        '''Prints a summary of the schedule'''
        print(f'Schedule: {self.title}')
        print(f'Start: {self.start}')
        print(f'End: {self.end}')
        print(f'Duration: {self.duration.days} days')
        print(f'Number of employees: {self.num_employees}')
        print(f'Number of shifts: {self.num_shifts} ({len([shift for shift in self.shifts if len(shift.employees) > 0])}/{len([shift for shift in self.shifts])})')
        print("Shift type (Assigned / Total):")
        for shift_type in self.shift_types:
            print(f'   - {shift_type}: {len([shift for shift in self.shifts if shift.type == shift_type])} ({len([shift for shift in self.shifts if shift.type == shift_type and len(shift.employees) > 0])}/{len([shift for shift in self.shifts if shift.type == shift_type])})')
        print(f'Number of holidays: {self.num_holidays}')
        print(f'Number of working days: {self.num_days - self.num_holidays}')

    # TODO: Complete the visualization function
    def visualize(self):
        '''Visualize schedule with timeline for each day'''
        assert self.start is not None and self.end is not None, 'Start and end date must be set'
        assert len(self.shifts) > 0, 'No shifts in the schedule'

        shifts = self.shifts
        shift_types = self.shift_types
        df_shifts = pd.DataFrame({
            'title': [shift.title for shift in shifts],
            'start': [shift.start for shift in shifts],
            'end': [shift.end for shift in shifts],
            'type': [shift.type for shift in shifts]
        }).sort_values(by='start')
        
        # plot shifts timeline with plotly express
        fig = px.timeline(
            df_shifts, 
            x_start='start', 
            x_end='end', 
            y='type',
            color='type',
            labels={'title': 'Shifts'},
            title='Shifts Timeline',
            category_orders= {'type': list(shift_types)}
        )
        # fig.update_yaxes(categoryorder='total ascending')
        fig.show()

        tasks = self.tasks
        df_tasks = pd.DataFrame({
            'Task': [task.title for task in tasks],
            'Start': [task.start for task in tasks],
            'End': [task.end for task in tasks],
            'Employee': [task.user[0].display_name if len(task.user) > 0 else 'Unassigned' for task in tasks],
        }).sort_values(by='Start')
        fig = px.timeline(
            df_tasks, 
            x_start='Start', 
            x_end='End', 
            y='Employee',
            color='Employee',
            labels={'Task': 'Tasks'},
            hover_data={'Task': True, 'Start': True, 'End': True, 'Employee': True},
            title='Tasks Timeline',
            category_orders= {'Employee': [employee.display_name for employee in self.employees]}
        )
        # fig.update_yaxes(categoryorder='total ascending')
        fig.show()
        

            
       

    def display_table(self):
        assert self.start is not None and self.end is not None, 'Start and end date must be set'
        assert len(self.shifts) > 0, 'No shifts in the schedule'
        dates = [date.date() for date in pd.date_range(self.start, self.end, freq='D')]
        shifts = self.shifts
        shift_types = self.shift_types
        employees = self.employees


        # Create a dataframe with the dates as the index and the shift types as the columns
        shift_schedule = pd.DataFrame(index=dates, columns=[shift_type for shift_type in shift_types])
        shift_by_type = {}
        # Optimized version
        for shift in shifts:
            if shift.type in shift_by_type:
                shift_by_type[shift.type].append(shift)
            else:
                shift_by_type[shift.type] = [shift]

        # Fill the dataframe with the employees assigned to each shift, if no shift is assigned, fill with 'Unassigned'
        for date in dates:
            for shift_type in shift_by_type:
                for shift in shift_by_type[shift_type]:
                    if shift.date == date:
                        if len(shift.employees) == 0:
                            shift_schedule.loc[date, shift_type] = 'Unassigned'
                        elif len(shift.employees) == 1:
                            shift_schedule.loc[date, shift_type] = shift.employees[0].first_name
                        elif len(shift.employees) > 1:
                            shift_schedule.loc[date, shift_type] = [employee.first_name for employee in shift.employees]
        
        # Fill nan values with '' (empty string)
        shift_schedule = shift_schedule.fillna(' ')

        # Display the table
        print(shift_schedule)

    # TODO: Fix  this later
    def to_sheet_values(self) -> list[list]:
        '''Convert schedule to list of list for google sheet'''
        

        dates = [date.date() for date in pd.date_range(self.start, self.end, freq='D')]
        shifts = self.shifts
        shift_types = self.shift_types
        employees = self.employees
        
        shift_schedule = pd.DataFrame(index=dates, columns=[shift_type for shift_type in shift_types])
        shift_by_type = {}
        # Optimized version
        for shift in shifts:
            if shift.type in shift_by_type:
                shift_by_type[shift.type].append(shift)
            else:
                shift_by_type[shift.type] = [shift]

        # Fill the dataframe with the employees assigned to each shift, if no shift is assigned, fill with 'Unassigned'
        for date in dates:
            for shift_type in shift_by_type:
                for shift in shift_by_type[shift_type]:
                    if shift.start.date() == date:
                        if len(shift.employees) == 0:
                            shift_schedule.loc[date, shift_type] = 'Unassigned'
                        elif len(shift.employees) == 1:
                            shift_schedule.loc[date, shift_type] = shift.employees[0].abbreviation
                        elif len(shift.employees) > 1:
                            shift_schedule.loc[date, shift_type] = str([employee.abbreviation for employee in shift.employees])
        
        # Fill nan values with '' (empty string)
        shift_schedule = shift_schedule.fillna('')

        # Reorder the columns
        columns = ['service night', 'mc', 'service1', 'service1+', 'service2', 'service2+', 'teaching', 'ems', 'observe', 'amd', 'avd']
        shift_schedule = shift_schedule[columns].values.tolist()

        return shift_schedule

        






