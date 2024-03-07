from datetime import datetime

class Event:
    def __init__(self, start: datetime, end: datetime, title: str, users: list = [], description: str = ''):
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
    

class Task(Event):
    def __init__(self, start: datetime, end: datetime, title: str, users: list = [], description: str = ''):
        super().__init__(start, end, title, users, description = description)

    def __repr__(self):
        return f'{self.title} starts at {self.start} and ends at {self.end}'
    

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


class Schedule:
    def __init__(self, 
                title: str, 
                start: datetime,
                end: datetime,
                description: str = '', 
                employees: list = [], 
                shifts: list = [], 
                tasks: list = []):
        self.title = title
        self.start = start
        self.end = end
        self.description = description
        self.employees = employees
        self.shifts = shifts
        self.tasks = tasks
        self.events = shifts + tasks

    def add_employee(self, employee: Employee):
        self.employees.append(employee)

    def add_shift(self, shift: Shift):
        self.shifts.append(shift)
        self.events.append(shift)

    def add_task(self, task: Task):
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
    
    # function: visualize schedule as a table

