from datetime import datetime, timedelta
import uuid
from ortools.sat.python import cp_model
import pandas as pd
import pickle
import csv
# from IPython.display import clear_output
import math
import numpy as np


class Employee:
    def __init__(self, first_name: str, last_name: str, role: str = 'Uncategorized', abbreviation: str = ''):
        assert len(first_name) > 0, 'First name cannot be empty'
        assert len(last_name) > 0, 'Last name cannot be empty'
        assert len(role) > 0, 'Role cannot be empty'

        self.first_name = first_name
        self.last_name = last_name
        self.name = first_name + " " + last_name
        self.abbreviation = abbreviation
        self.role = role
        self._id = uuid.uuid4()
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self.all_tasks = []

    @property
    def full_name(self) -> str:
        return self.name

    @property
    def shifts(self) -> list:
        shifts = []
        for task in self.all_tasks:
            if isinstance(task, Shift):
                shifts.append(task)
        return shifts

    @property
    def tasks(self) -> list:
        tasks = []
        for task in self.all_tasks:
            if not isinstance(task, Shift) and isinstance(task, Task):
                tasks.append(task)
        return tasks

    def __repr__(self) -> str:
        return f"Employee('{self.name}', '{self.role}', {self.all_tasks})"

    def add_task(self, task):
        # Check if task is already in the list
        if task in self.all_tasks:
            raise Exception('Task is already in the list')
        # Check if task start_time & end_time is not overlapping with any other tasks #TODO: Currently disable
        # for t in self.all_tasks:
        #     if (task.start_time >= t.start_time and task.start_time < t.end_time) or (task.end_time > t.start_time and task.end_time <= t.end_time):
        #         raise Exception('Task overlaps with another task')

        self.all_tasks.append(task)
        self._updated_at = datetime.now()
    
    def remove_task(self, task):
        # Check if task is in the list
        if task not in self.all_tasks:
            raise Exception('Task is not in the list')
        self.all_tasks.remove(task)
        self._updated_at = datetime.now()

    def reset_tasks(self):
        self.all_tasks = []
        self._updated_at = datetime.now()

    #TODO: fix task, all_tasks, and shifts
    def is_available(self, task):
        # Check if task start_time & end_time is not overlapping with any other tasks
        for t in self.tasks:
            if (task.start_time >= t.start_time and task.start_time < t.end_time) or (task.end_time > t.start_time and task.end_time <= t.end_time):
                return False
        return True
    
    def is_available_date(self, date: datetime):
        for task in self.all_tasks:
            if task.date == date:
                return False
        return True

    @classmethod
    def from_csv(cls, file_name: str) -> list:
        employees = []
        with open(file_name, 'r') as f:
            reader = csv.reader(f)
            header = next(reader) # save the header for indexing
            for row in reader:
                employees.append(cls(row[header.index('first_name')], row[header.index('last_name')], row[header.index('role')]))
            
        return employees


class Task:
    def __init__(self, name: str, description: str, start_time: datetime, duration: timedelta):
        
        self.name = name
        self.description = description
        assert duration >= timedelta(minutes=0), "duration must be greater than or equal to 0"
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self._id = uuid.uuid4()
        self._created_at = datetime.now()
        self._updated_at = datetime.now()

    def __repr__(self) -> str:
        return self.name + " " + str(self.start_time) + " " + str(self.end_time)

    # Check if the task is overlapping with another task
    def overlap(self, other) -> bool:
        return self.start_time < other.end_time and other.start_time < self.end_time
    
    # Check if the task is overlapping with a list of tasks
    def overlap_list(self, task_list) -> bool:
        for task in task_list:
            if self.overlap(task):
                return True
        return False
    
    @property
    def date(self):
        return self.start_time.day
    

class Shift(Task):

    def __init__(self, name: str, description: str, duration: timedelta, start_time: datetime, shift_type: str, min_employees: int = 1, max_employees: int = 1):
        super().__init__(name, description, start_time, duration)
        self.shift_type = str.lower(shift_type)
        assert min_employees <= max_employees, "min_employees must be less than or equal to max_employees"
        assert min_employees >= 0, "min_employees must be greater than or equal to 0"
        assert max_employees >= 0, "max_employees must be greater than or equal to 0"
        self.min_employees = min_employees
        self.max_employees = max_employees
        self.employees = []
        # self.date = start_time.date()

    @property
    def day(self):
        return self.start_time.day
    
    @property
    def date(self):
        return self.start_time.date()

    @property
    def type(self):
        return self.shift_type

    def add_employee(self, employee):
        # Check if employee is already in the list
        if employee in self.employees:
            raise Exception('Employee is already in the list')
        self.employees.append(employee)
        self._updated_at = datetime.now()

    def remove_employee(self, employee):
        # Check if employee is in the list
        if employee not in self.employees:
            raise Exception('Employee is not in the list')
        self.employees.remove(employee)
        self._updated_at = datetime.now()

    def reset_employees(self):
        self.employees = []
        self._updated_at = datetime.now()



# Solution printer.
class ShiftSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shift_vars: dict, shifts: list[Shift], employees: list[Employee], penalties, start_time: datetime, end_time: datetime):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__shift_vars = shift_vars
        self.__shifts = shifts
        self.__employees = employees
        self.__shift_types = set([s.type for s in shifts])
        self.__employee_roles = set([e.role for e in employees])
        self.__solution_count = 0
        self.__start_time = start_time
        self.__end_time = end_time

    @property
    def dates(self):
        return pd.date_range(self.__start_time, self.__end_time, freq='D')

    def on_solution_callback(self):

        # Create a dataframe with the dates as the index and the shift types as the columns
        shift_schedule = pd.DataFrame(index=self.dates, columns=[shift_type for shift_type in self.__shift_types])
        shift_by_type = {}
        # Optimized version
        for shift in self.__shifts:
            if shift.shift_type in shift_by_type:
                shift_by_type[shift.shift_type].append(shift)
            else:
                shift_by_type[shift.shift_type] = [shift]

        # Fill the dataframe with the employees assigned to each shift, if no shift is assigned, fill with 'Unassigned'
        for date in self.dates:
            for shift_type in shift_by_type:
                for shift in shift_by_type[shift_type]:
                    if shift.start_time.date() == date:
                        shift_schedule.loc[date, shift_type] = [employee.first_name for employee in self.__employees if self.Value(self.__shift_vars[(shift, employee)]) == 1]

        # Fill nan values with '' (empty string)
        shift_schedule = shift_schedule.fillna('')
    
        self.__solution_count += 1

        
        schedule_workload = pd.DataFrame(index=[employee.name for employee in self.__employees], columns=[shift_type for shift_type in self.__shift_types])
            
        for employee in self.__employees:
            for shift_type in self.__shift_types:
                schedule_workload.loc[employee.name, shift_type] = len([shift for shift in shift_by_type[shift_type] if self.Value(self.__shift_vars[(shift, employee)]) == 1])
        
        # clear_output(wait=True)
        print('Solution %i' % self.__solution_count)
        print('  Objective value = %i' % self.ObjectiveValue())
        print(shift_schedule)
        print(schedule_workload)

    def solution_count(self):
        return self.__solution_count



class Schedule:
    def __init__(self, name: str, start_time: datetime, end_time: datetime):
        assert start_time < end_time, 'Start time must be before end time'
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.employees = list[Employee]()
        self.shifts = list[Shift]()

        self._holidays = self.get_weekends(start_time, end_time)

        self.__id = uuid.uuid4()
        self.__created_at = datetime.now()
        self.__updated_at = datetime.now()

        self.__model = cp_model.CpModel()
        self.__shift_vars = {}
        self.__penalties = 0

        self.__logs = []

        # Constraint
        self.__shift_group_sum_employee = {}
        self.__shift_sum_employee = {}

        # Objective
        self.__shift_preference = {}
        
        
    @property
    def solution_printer(self):
        return ShiftSolutionPrinter(self.__shift_vars, self.shifts, self.employees, self.__penalties, self.start_time, self.end_time)
    
    @property
    def penalty(self):
        return self.__penalties
    
    @property
    def dates(self) -> list[datetime]:
        return [self.start_time + timedelta(days=x) for x in range(self.duration.days + 1)]
    
    @property
    def days(self) -> list:
        return [date.date() for date in self.dates]

    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time

    @property
    def holidays(self) -> list[datetime]:
        return self._holidays
    
    @property
    def holiday_dates(self) -> list:
        return [holiday.date() for holiday in self.holidays]

    @property
    def roles(self) -> set:
        return(set([employee.role for employee in self.employees]))

    @property
    def shift_types(self) -> set:
        return set([shift.shift_type for shift in self.shifts])
    
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
    
    # TODO: This function is very slow :(, need to optimize)
    def get_shifts_by_date(self, date: datetime) -> list[Shift]:
        return [shift for shift in self.shifts if shift.start_time.date() == date.date()]
    
    
    def shift_per_employee(self, shift_type) -> float:
        average = sum([shift.shift_type == shift_type for shift in self.shifts]) / len(self.employees)
        return average

    def info(self):
        print(f"Schedule: {self.name}")
        print(f"Start Time: {self.start_time}")
        print(f"End Time: {self.end_time}")
        print(f"Number of days: {self.duration.days + 1}")
        print(f"Number of holidays: {len(self.holidays)}")
        print(f"Roles: {self.roles}")
        print(f"Shift Types: {self.shift_types}")

        #Schedule statistics
        print(f"Number of Employees: {len(self.employees)}")
        print(f"Number of Shifts: {len(self.shifts)}")
        for shift_type in self.shift_types:
            print(f"Number of {shift_type} shifts: {len([shift for shift in self.shifts if shift.shift_type == shift_type])}")
            print(f"Number of {shift_type} shifts per employee: {self.shift_per_employee(shift_type)}")

    def add_holiday(self, date: datetime) -> None:
        # Check if date is in dates 
        if date not in self.dates:
            raise ValueError('Date is not in schedule')
        # Check if date is already a holiday
        if date in self._holidays:
            # raise ValueError('Date is already a holiday')
            print(f'{date} is already a holiday')
        else:
            self._holidays.append(date)
            self.__updated_at = datetime.now()

    def remove_holiday(self, date: datetime) -> None:
        # Check if date is in holidays
        if date in self._holidays:
            self._holidays.remove(date)
            self.__updated_at = datetime.now()
        else:
            raise ValueError('Date is not a holiday')

    @staticmethod
    def get_weekends(start_time: datetime, end_time: datetime) -> list[datetime]:
        return [start_time + timedelta(days=x) for x in range((end_time - start_time).days + 1) if (start_time + timedelta(days=x)).weekday() in [5, 6]]

    def __repr__(self) -> str:
        return f'{self.name} From {self.start_time.isoformat()} to {self.end_time.isoformat()}'

    def __str__(self) -> str:
        return f'{self.name} From {self.start_time.isoformat()} to {self.end_time.isoformat()}'

    def reset(self) -> None:
        self.employees = []
        self.shifts = []
 
    def add_employee(self, employee) -> object:
        self.employees.append(employee)
        self.__updated_at = datetime.now()
        return employee

    def add_shift(self, shift) -> object:
        self.shifts.append(shift)
        self.__updated_at = datetime.now()
        return shift
    
    def add_shifts(self, shift: Shift, holiday = False, until = None) -> None:
        if holiday:
            dates = [date for date in self.dates if date.date() >= shift.start_time.date()]
        else:
            dates = [date for date in self.dates if date not in self.holidays and date.date() >= shift.start_time.date()]
        
        for date in dates:
            if until is None:
                start_time = datetime.combine(date, shift.start_time.time())
                self.add_shift(Shift(name=shift.name + ' ' + str(start_time.date()), description=shift.description, start_time=start_time, duration=shift.duration, shift_type=shift.shift_type,
                                    min_employees=shift.min_employees, max_employees=shift.max_employees))
            elif date <= until:
                start_time = datetime.combine(date, shift.start_time.time())
                self.add_shift(Shift(name=shift.name + ' ' + str(start_time.date()), description=shift.description, start_time=start_time, duration=shift.duration, shift_type=shift.shift_type,
                                    min_employees=shift.min_employees, max_employees=shift.max_employees))
            else:
                break
                
    def remove_employee(self, employee) -> None:
        self.employees.remove(employee)
        self.__updated_at = datetime.now()

    def remove_shift(self, shift) -> None:
        self.shifts.remove(shift)
        self.__updated_at = datetime.now()

    def assign_shift(self, shift: Shift, employee: Employee) -> None:
        shift.add_employee(employee)
        employee.add_task(shift)
        self.__updated_at = datetime.now()

    def add_total_shift_constraint(self, employee_abbreviation: str, total_shifts: int) -> None:
        self.__shift_group_sum_employee[employee_abbreviation] = total_shifts
        print(self.__shift_group_sum_employee)

    def add_shift_constraint(self, employee_abbreviation: str, shift_type: str, total_shifts: int) -> None:
        self.__shift_sum_employee[employee_abbreviation, shift_type] = total_shifts
        print(self.__shift_sum_employee)

    def add_shift_preference(self, employee_abbreviation: str, morning_preference: bool, afternoon_preference: bool) -> None:
        if morning_preference:
            self.__shift_preference[employee_abbreviation] = 'morning'
        elif afternoon_preference:
            self.__shift_preference[employee_abbreviation] = 'afternoon'
        else:
            self.__shift_preference[employee_abbreviation] = None

    def show(self, format = 'text', group_by = 'shift type') -> None:        
        
        if format == 'text':
            self.__display_text()
        elif format == 'table':
            self.__display_table(group_by=group_by)
        else:
            raise Exception('Invalid format')

    def __display_text(self) -> None:
        print('Schedule Name: {}'.format(self.name))
        print('Start Time: {}'.format(self.start_time))
        print('End Time: {}'.format(self.end_time))
        print('Duration: {}'.format(self.duration))
        print('Employees: {}'.format(self.employees))
        print('Shifts: {}'.format(self.shifts))
        print('Created At: {}'.format(self.__created_at))
        print('Updated At: {}'.format(self.__updated_at))

    def __display_table(self, group_by = 'shift type') -> pd.DataFrame:
        dates = [date.date() for date in pd.date_range(self.start_time, self.end_time, freq='D')]
        shifts = self.shifts
        shift_types = self.shift_types
        employees = self.employees

        if group_by == 'shift':
            # Create a dataframe with the dates as the index and the shifts as the columns
            shift_schedule = pd.DataFrame(index=dates, columns=[shift.name for shift in shifts])

            # Fill the dataframe with the employees assigned to each shift, if no shift is assigned, fill with 'None'
            # If a shift is assigned to multiple employees, fill with list of employees
            # If there're no shifts on a given day, fill with "-"
            for date in dates:
                for shift in shifts:
                    if shift.start_time.date() == date:
                        if len(shift.employees) == 0:
                            shift_schedule.loc[date, shift.name] = 'None'
                        elif len(shift.employees) == 1:
                            shift_schedule.loc[date, shift.name] = shift.employees[0].first_name
                        else:
                            shift_schedule.loc[date, shift.name] = [employee.first_name for employee in shift.employees]
                    else:
                        shift_schedule.loc[date, shift.name] = '-'
        elif group_by == 'shift type':
            # Create a dataframe with the dates as the index and the shift types as the columns
            shift_schedule = pd.DataFrame(index=dates, columns=[shift_type for shift_type in shift_types])
            shift_by_type = {}
            # Optimized version
            for shift in shifts:
                if shift.shift_type in shift_by_type:
                    shift_by_type[shift.shift_type].append(shift)
                else:
                    shift_by_type[shift.shift_type] = [shift]

            # Fill the dataframe with the employees assigned to each shift, if no shift is assigned, fill with 'Unassigned'
            for date in dates:
                for shift_type in shift_by_type:
                    for shift in shift_by_type[shift_type]:
                        if shift.start_time.date() == date:
                            if len(shift.employees) == 0:
                                shift_schedule.loc[date, shift_type] = 'Unassigned'
                            elif len(shift.employees) == 1:
                                shift_schedule.loc[date, shift_type] = shift.employees[0].first_name
                            elif len(shift.employees) > 1:
                                shift_schedule.loc[date, shift_type] = [employee.first_name for employee in shift.employees]
            
            # Fill nan values with '' (empty string)
            shift_schedule = shift_schedule.fillna(' ')

        elif group_by == 'workload':
            # Create a dataframe with the employees as the index and the shift types as columns
            shift_schedule = pd.DataFrame(index=[employee.name for employee in employees], columns=[shift_type for shift_type in shift_types])
            
            for employee in self.employees:
                for shift_type in shift_types:
                    shift_schedule.loc[employee.name, shift_type] = len([shift for shift in employee.shifts if shift.shift_type == shift_type])
                shift_schedule.loc[employee.name, 'Total'] = len(employee.shifts)
      
        else:
            raise ValueError(f'Invalid value for group_by: {group_by}')
        
        
        # Display the dataframe
        print(shift_schedule)

        return shift_schedule
    
    def save(self, file_name):
        with open(file_name, 'wb') as f:
            pickle.dump(self, f)

    def to_csv(self, path):
        self.__display_table(group_by="shift type").to_csv(path + '/schedule.csv')
        self.__display_table(group_by="workload").to_csv(path + '/workload.csv')

    @staticmethod
    def load(file_name):
        with open(file_name, 'rb') as f:
            return pickle.load(f)

    @staticmethod
    def __negated_bounded_span(works, start, length):
        """Filters an isolated sub-sequence of variables assined to True.
    Extract the span of Boolean variables [start, start + length), negate them,
    and if there is variables to the left/right of this span, surround the span by
    them in non negated form.
    Args:
        works: a list of variables to extract the span from.
        start: the start to the span.
        length: the length of the span.
    Returns:
        a list of variables which conjunction will be false if the sub-list is
        assigned to True, and correctly bounded by variables assigned to False,
        or by the start or end of works.
    """
        sequence = []
        # Left border (start of works, or works[start - 1])
        if start > 0:
            sequence.append(works[start - 1])
        for i in range(length):
            sequence.append(works[start + i].Not())
        # Right border (end of works or works[start + length])
        if start + length < len(works):
            sequence.append(works[start + length])
        return sequence

    @staticmethod
    def __add_soft_sequence_constraint(model, works, hard_min, soft_min, min_cost,
                                    soft_max, hard_max, max_cost, prefix):
    
        cost_literals = []
        cost_coefficients = []

        # Forbid sequences that are too short.
        for length in range(1, hard_min):
            for start in range(len(works) - length + 1):
                model.AddBoolOr(Schedule.__negated_bounded_span(works, start, length))

        # Penalize sequences that are below the soft limit.
        if min_cost > 0:
            for length in range(hard_min, soft_min):
                for start in range(len(works) - length + 1):
                    span = Schedule.__negated_bounded_span(works, start, length)
                    name = ': under_span(start=%i, length=%i)' % (start, length)
                    lit = model.NewBoolVar(prefix + name)
                    span.append(lit)
                    model.AddBoolOr(span)
                    cost_literals.append(lit)
                    # We filter exactly the sequence with a short length.
                    # The penalty is proportional to the delta with soft_min.
                    cost_coefficients.append(min_cost * (soft_min - length))

        # Penalize sequences that are above the soft limit.
        if max_cost > 0:
            for length in range(soft_max + 1, hard_max + 1):
                for start in range(len(works) - length + 1):
                    span = Schedule.__negated_bounded_span(works, start, length)
                    name = ': over_span(start=%i, length=%i)' % (start, length)
                    lit = model.NewBoolVar(prefix + name)
                    span.append(lit)
                    model.AddBoolOr(span)
                    cost_literals.append(lit)
                    # Cost paid is max_cost * excess length.
                    cost_coefficients.append(max_cost * (length - soft_max))

        # Just forbid any sequence of true variables with length hard_max + 1
        for start in range(len(works) - hard_max):
            model.AddBoolOr(
                [works[i].Not() for i in range(start, start + hard_max + 1)])
        return cost_literals, cost_coefficients

    @staticmethod
    def __add_soft_sum_constraint(model, works, hard_min, soft_min, min_cost,
                                soft_max, hard_max, max_cost, prefix):
        
        cost_variables = []
        cost_coefficients = []
        sum_var = model.NewIntVar(hard_min, hard_max, '')
        # This adds the hard constraints on the sum.
        model.Add(sum_var == sum(works))
        if soft_min > hard_min and min_cost > 0:
            delta = model.NewIntVar(-len(works), len(works), '')
            model.Add(delta == soft_min - sum_var)
            # TODO(user): Compare efficiency with only excess >= soft_min - sum_var.
            excess = model.NewIntVar(0, 7, prefix + ': under_sum')
            model.AddMaxEquality(excess, [delta, 0])
            cost_variables.append(excess)
            cost_coefficients.append(min_cost)

        # Penalize sums above the soft_max target.
        if soft_max < hard_max and max_cost > 0:
            delta = model.NewIntVar(-7, 7, '')
            model.Add(delta == sum_var - soft_max)
            excess = model.NewIntVar(0, 7, prefix + ': over_sum')
            model.AddMaxEquality(excess, [delta, 0])
            cost_variables.append(excess)
            cost_coefficients.append(max_cost)

        return cost_variables, cost_coefficients
    

    def solve(self, time_limit=60, verbose=True):
        # ------------------------ Variable ---------------------------
        self.__shift_vars = {}
        for shift in self.shifts:
            for employee in self.employees:
                self.__shift_vars[(shift, employee)] = self.__model.NewBoolVar('shift_{}_employee_{}'.format(shift.name, employee.name)) #

        # ------------------------ Constraints -> Rules ---------------------------

        # Solve constraint one by one, exit if there's no solution
        date_constraints = {}
        employee_constraints = {}

        # constraint should look like this:
        # constraints = {
        # date: [list of constraints]],
        # date: [list of constraints]],
        # ...}

       
        for date in self.days:
            date_constraints[date] = []
        
        for employee in self.employees:
            employee_constraints[employee] = []
        
 
        # [1] Each shift must be assigned to employees more than or equal to min_employees, and less than or equal to max_employees
        for shift in self.shifts:
            date_constraints[shift.date].append(sum([self.__shift_vars[(shift, employee)] for employee in self.employees]) >= shift.min_employees)
            date_constraints[shift.date].append(sum([self.__shift_vars[(shift, employee)] for employee in self.employees]) <= shift.max_employees)


        # [2] If the shift is assigned to employees, fixed the shift assigned to the employees
        fixed_shifts = []
        ls_fixed_shifts = []
        for shift in self.shifts:
            for employee in shift.employees:
                fixed_shifts.append((shift, employee))
                ls_fixed_shifts.append(shift)
        for shift, employee in fixed_shifts:
            date_constraints[shift.date].append(self.__shift_vars[(shift, employee)] == 1)
            
        ls_not_fixed_shifts = [shift for shift in self.shifts if shift not in ls_fixed_shifts]
        # print("Not fix:", ls_not_fixed_shifts)

        # [3] The shift should only be assigned to the employees who are available (Compare to employee's tasks), except for fixed shifts
        for date in self.dates:
            for shift in self.get_shifts_by_date(date):
                for employee in self.employees:
                    if not employee.is_available(shift) and (shift, employee) not in fixed_shifts:
                        date_constraints[shift.date].append(self.__shift_vars[(shift, employee)] == 0)
        

        # [4.1] Some shifts cannot be assigned to the same employee in the same day, represent with a logical matrix, exclude fixed shifts
        shift_types_matrix = {
            'labels' : ['s1', 's1+', 'mc', 's2', 's2+', 'observe', 'ems', 'amd', 'avd'],
            'matrix': [
              # s1 s1+ mc s2 s2+ ob em amd avd
                [0, 0, 0, 0, 0, 0, 0, 1, 0], # s1
                [0, 0, 0, 0, 0, 1, 1, 1, 1], # s1+
                [0, 0, 0, 1, 1, 0, 0, 1, 1], # mc
                [0, 0, 1, 0, 0, 0, 0, 1, 0], # s2
                [0, 0, 1, 0, 0, 1, 1, 1, 1], # s2+
                [0, 1, 0, 0, 1, 0, 0, 1, 1], # ob
                [0, 1, 0, 0, 1, 0, 0, 1, 1], # em
                [1, 1, 1, 1, 1, 1, 1, 0, 0], # amd
                [0, 1, 1, 0, 1, 1, 1, 0, 0]  # avd
            ]
        }

        shift_labels = shift_types_matrix['labels']
        matrix = shift_types_matrix['matrix']
        for date in self.dates:
            shifts = self.get_shifts_by_date(date) # exclude fixed shifts
            not_fix = [shift for shift in shifts if shift.employees == []]
            # if shifts[0].date.day == 4:
            #     print("not fix2:", not_fix)
            for shift1 in shifts:
                for shift2 in not_fix:
                    
                    if shift1 == shift2:
                        continue
                    if shift1.type in shift_labels and shift2.type in shift_labels:
                        # if shift1.date.day == 4:
                        #     print(shift1, shift2)
                        i = shift_labels.index(shift1.type)
                        j = shift_labels.index(shift2.type)
                        if not matrix[i][j]:
                            for employee in self.employees:
                                date_constraints[shift1.date].append(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1)


        # [4.2] If an employee available lower than minimum number of shift, they can work s1 and s2 shifts on the same day


        # [4.3] Employee cannot work more than 2 shifts per day
        for date in self.days:
            for employee in self.employees:
                date_constraints[date].append(sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.start_time.date() == date]) <= 2)

        #[5] Fair distribution of shifts per employee per shift type
        # TODO: Create an automatic way to feed the shift_group_sum, may be 'increment constraint with maximize the minimum'?
        shift_group_sum = {
            ('max',('mc')) : math.floor(self.shift_per_employee('mc'))+1,
            ('min',('mc')) : math.floor(self.shift_per_employee('mc')),
            ('max',('amd')) : math.floor(self.shift_per_employee('amd'))+1,
            ('min',('amd')) : math.floor(self.shift_per_employee('amd')),
            ('max',('avd')) : math.floor(self.shift_per_employee('avd'))+1,
            ('min',('avd')) : math.floor(self.shift_per_employee('avd')),
            ('max',('s1', 's2')) : math.floor(self.shift_per_employee('s1') + self.shift_per_employee('s2'))+1,
            ('min',('s1', 's2')) : math.floor(self.shift_per_employee('s1') + self.shift_per_employee('s2')),
            ('max',('s1', 's1+', 's2', 's2+')) : math.floor(self.shift_per_employee('s1') + self.shift_per_employee('s1+') + self.shift_per_employee('s2') + self.shift_per_employee('s2+'))+1,
            ('min',('s1', 's1+', 's2', 's2+')) : math.floor(self.shift_per_employee('s1') + self.shift_per_employee('s1+') + self.shift_per_employee('s2') + self.shift_per_employee('s2+'))-2,
        }

        print(shift_group_sum)

        for employee in self.employees:
            employee_constraints[employee] = []
            for group in shift_group_sum:
                shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in group[1]]
                if group[0] == 'max':
                    employee_constraints[employee].append(sum(shifts) <= shift_group_sum[group])
                elif group[0] == 'min':
                    employee_constraints[employee].append(sum(shifts) >= shift_group_sum[group])
       
        # [ุ6] Manual set number of shifts per employee
        shift_group_sum_employee = {
            ('s1', 's2', 's1+', 's2+'): self.__shift_group_sum_employee,
            }

        for group in shift_group_sum_employee:
            for e in shift_group_sum_employee[group]:
                employee = [employee for employee in self.employees if employee.abbreviation == e][0]
                shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in group]
                employee_constraints[employee].append(sum(shifts) == shift_group_sum_employee[group][e])

        


        # [x] Equalize holiday shifts per employee -> Moved to objective section
        # holiday_shifts = [shift for shift in self.shifts if shift.date in self.holiday_dates]
        # for employee in self.employees:
        #     employee_constraints[employee].append(sum([self.__shift_vars[(shift, employee)] for shift in holiday_shifts]) >= math.floor(len(holiday_shifts) / len(self.employees)))
        #     employee_constraints[employee].append(sum([self.__shift_vars[(shift, employee)] for shift in holiday_shifts]) <= math.floor(len(holiday_shifts) / len(self.employees)) + 1)
        


        # ------------------------ Objectives -> Optimization goals ---------------------------

        objectives = {}

        # Objective look like this:
        # objectives = {
            # objective name: [objective values],
            # objective name: [objective values],
            # ...}

        # [1] Distribution of workload, Minimize the number of shifts assigned to employees on the same day, 1 shift per employee per day if possible
        for date in self.days:
            objectives[f'Minimize the number of shifts assigned to each employee on {date}'] = []
            for employee in self.employees:
                objectives[f'Minimize the number of shifts assigned to each employee on {date}'].append(sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.start_time.date() == date]) <= 1)

        # [2] Avoid working on the consecutive days
        shift_group_for_distribution = [
            ('s1', 's2', 's1+', 's2+'),
            ('mc'),
            ('amd', 'avd'),
            ('avd')
        ]
        duration = 1 #days
        for employee in self.employees:
            for shift_type in shift_group_for_distribution:
                shifts = [shift for shift in self.shifts if shift.shift_type in shift_type] # Shifts = [shift1, shift2, ...] for each shift type
                for shift1 in shifts:
                    for shift2 in [shift for shift in shifts if shift != shift1 and shift.start_time > shift1.start_time and shift.start_time - shift1.start_time <= timedelta(days=duration)]:
                        objectives[f'Avoid working {shift_type} on the consecutive days for {employee.abbreviation} between {shift1.name} & {shift2.name}'] = []
                        objectives[f'Avoid working {shift_type} on the consecutive days for {employee.abbreviation} between {shift1.name} & {shift2.name}'].append(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1)


    
                

        # [3] Shift Preference, some employees prefer to work in the morning, some prefer to work in the afternoon
        # shift_preference = {
        #     'BC' : 'morning',
        #     'KL' : None,
        #     'UT' : 'afternoon'
        #     ...
        # }

        shift_preference = self.__shift_preference
        for employee in self.employees:
            if shift_preference[employee.abbreviation] is None:
                continue
            morning_shifts = sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['s1', 's1+']])
            afternoon_shifts = sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['s2', 's2+']])

            shift_diff = morning_shifts - afternoon_shifts if shift_preference[employee.abbreviation] == 'morning' else afternoon_shifts - morning_shifts
            objective_key = f'Shift preference for {employee.abbreviation} soft'

            # Add the soft constraint directly to the objective
            max = math.floor(self.shift_per_employee('s1') + self.shift_per_employee('s1+') + self.shift_per_employee('s2') + self.shift_per_employee('s2+'))+1
            for i in range(1, 5):
                objectives[objective_key + f', preference delta = {i}'] = []

            for i in range(1, 5):    
                objectives[objective_key + f', preference delta = {i}'].append(shift_diff >= i)

            # objective_key_hard = f'Shift preference for {employee.abbreviation} hard'
            # objectives[objective_key_hard] = []
            # value = morning_shifts == 0 if shift_preference[employee.abbreviation] == 'morning' else afternoon_shifts == 0
            # objectives[objective_key_hard].append(value)

        # # [4] Equalize holiday shifts per employee
        # holiday_shifts = [shift for shift in self.shifts if shift.date in self.holiday_dates]
        # for employee in self.employees:
        #     objectives[f'Equalize holiday shifts per employee for {employee.abbreviation}'] = []
        #     objectives[f'Equalize holiday shifts per employee for {employee.abbreviation}'].append(sum([self.__shift_vars[(shift, employee)] for shift in holiday_shifts]) >= math.floor(len(holiday_shifts) / len(self.employees)))
        #     objectives[f'Equalize holiday shifts per employee for {employee.abbreviation}'].append(sum([self.__shift_vars[(shift, employee)] for shift in holiday_shifts]) <= math.floor(len(holiday_shifts) / len(self.employees)) + 1)
        


    
        # TODO: Not work for now, fix this later
        # [x] Equal distribution of shifts per employee (per shift type)
        # for shift_type in self.shift_types:
        #     shifts_by_type = [shift for shift in self.shifts if shift.shift_type == shift_type]
        #     min_shifts = self.__model.NewIntVar(0, len(self.shifts), f'min_{shift_type}_shifts')
        #     employee_shifts = [self.__model.NewIntVar(0, len(shifts_by_type), f'{employee.name}_{shift_type}_shifts') for employee in self.employees]
        #     self.__model.Add(sum(employee_shifts) == len(shifts_by_type))
        #     self.__model.AddMinEquality(min_shifts, employee_shifts)
        #     objectives[f'Equal distribution of {shift_type} shifts per employee)'] = sum([min_shifts])

        # TODO: Not work for now, fix this later
        # [x] Distribution of workload, disperse the shift of each employee throughout the schedule, for each shift type
        # shift_group_for_distribution = [
        #     ('s1', 's2', 's1+', 's2+'),
        #     ('mc'),
        #     ('amd', 'avd'),
        #     ('avd')
        # ]
        # for employee in self.employees:
        #     for shift_type in shift_group_for_distribution:
        #         objectives[f'Distribution of {shift_type} workload for {employee.abbreviation} soft'] = []
        #         objectives[f'Distribution of {shift_type} workload for {employee.abbreviation} hard'] = []
        #         # Shifts = [shift1, shift2, ...] for each shift type
        #         shifts = [shift for shift in self.shifts if shift.shift_type in shift_type]
        #         # Shift Strata = [[shift1, shift2, ...], [shift3, shift4, ...], ...] to 'x' groups, which x = number of shifts per employee
        #         shift_strata = [shifts[i:i + len(shifts) // (math.floor(self.shift_per_employee(shift_type[0]))+1)] for i in range(0, len(shifts), len(shifts) // (math.floor(self.shift_per_employee(shift_type[0]))+1))]
        #         # Slide strata by 1, to create a list of shift groups

        #         for shift_group in shift_strata:
        #             # If the shift group is not empty
        #             if len(shift_group) > 0:
        #                 # Add the sum of the shifts in the group to the objective
        #                 objectives[f'Distribution of {shift_type} workload for {employee.abbreviation} soft'].append(sum([self.__shift_vars[(shift, employee)] for shift in shift_group]) <= 2)
        #                 # Add the sum of the shifts in the group to the objective
        #                 objectives[f'Distribution of {shift_type} workload for {employee.abbreviation} hard'].append(sum([self.__shift_vars[(shift, employee)] for shift in shift_group]) <= 1)
                    


        # ------------------------ Solve ---------------------------

        self.__logs.append('Begin solving for the schedule, with following rules:')
        self.__logs.append('Rule 1: Each shift must be assigned to employees more than or equal to min_employees, and less than or equal to max_employees')
        self.__logs.append('Rule 2: If the shift is assigned to employees, fixed the shift assigned to the employees')
        self.__logs.append('Rule 3: The shift should only be assigned to the employees who are available (Compare to employee\'s tasks), except for fixed shifts')
        self.__logs.append('Rule 4: Some shifts cannot be assigned to the same employee in the same day, represent with a logical matrix, exclude fixed shifts')
        self.__logs.append(f'Rule 5: Fair distribution of shifts per employee per shift type')
        for group in shift_group_sum:
            self.__logs.append(f'    {group[0]} shifts per employee per {group[1]} = {shift_group_sum[group]}')
        self.__logs.append(f'Rule 6: Manual set number of shifts per employee')
        for group in shift_group_sum_employee:
            for e in shift_group_sum_employee[group]:
                self.__logs.append(f'    {e} = {shift_group_sum_employee[group][e]}')
        self.__logs.append('')
        self.__logs.append('Result:')

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8
        
        # solve model with incremental constraints, if no solution, reset the model and add the constraints again, skip the date
        constraint_complete = True
        model_before_become_infeasible = cp_model.CpModel()

        try: 
            for date in self.days:
                model_before_become_infeasible.CopyFrom(self.__model)
                for constraint in date_constraints[date]:
                    self.__model.Add(constraint)
                status = solver.Solve(self.__model)
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    continue
                else:
                    self.__logs.append(f'❌ No solution found for {date}')
                    print(f'No solution found for {date}')
                    self.__model.CopyFrom(model_before_become_infeasible)
                    constraint_complete = False
                    continue 

            for employee in self.employees:
                model_before_become_infeasible.CopyFrom(self.__model)
                for constraint in employee_constraints[employee]:
                    self.__model.Add(constraint)
                status = solver.Solve(self.__model)
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    continue
                else:
                    self.__logs.append(f'❌ No solution found for {employee.abbreviation}')
                    print(f'No solution found for {employee.abbreviation}')
                    self.__model.CopyFrom(model_before_become_infeasible)
                    constraint_complete = False
                    continue

            # Add objectives, if no solution, reset the model and add the new objectives, skip the objective
            if constraint_complete:
                self.__logs.append('✅︎ All rules are satisfied, now optimizing the schedule with following objectives:')
                print('All constraints are satisfied, adding objectives ...')
                for objective_name, objective_group in objectives.items():
                    model_before_become_infeasible.CopyFrom(self.__model)
                    for objective in objective_group:
                        self.__model.Add(objective)
                    status = solver.Solve(self.__model)
                    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                        self.__logs.append('✅︎ Objective: {}'.format(objective_name))
                        continue
                    else:
                        print(f'No solution found for {objective_name}')
                        self.__logs.append('❌ Objective: {}'.format(objective_name))
                        self.__model.CopyFrom(model_before_become_infeasible)
                        continue
            else:
                self.__logs.append("❌ The schedule is not optimized, because the rules are not satisfied")

            
        except Exception as e:
            self.__logs.append("❌ The program exited with an error")
            self.__logs.append("Error: {}".format(e))

        # Update the shifts and employees
        for shift in self.shifts:
            for employee in self.employees:
                try:
                    if solver.Value(self.__shift_vars[(shift, employee)]) == 1:
                    # print(f'{shift.name} is assigned to {employee.name}')
                        shift.add_employee(employee)
                        employee.add_task(shift)
                except Exception as e:
                        pass
                
        self.__logs.append("")                
        self.__logs.append("Schedule Updated!")                




            # for objective_name, objective_value in objectives.items():
            #     self.__model.Maximize(objective_value)
            #     status = solver.Solve(self.__model)
            #     print(f'Objective: {objective_name} = {solver.ObjectiveValue()}')

            #     # Save objective satisfaction
            #     self.__model.Add(objective_value >= round(solver.ObjectiveValue()))

    # legacy version
    def solve1(self, time_limit=60, verbose=True):
        """Solves the schedule using the CP-SAT solver.

        Args:
            time_limit: The time limit in seconds.
            verbose: If True, prints the solver output.
        """
        # ------------------------ Variable ---------------------------
        self.__shift_vars = {}
        for shift in self.shifts:
            for employee in self.employees:
                self.__shift_vars[(shift, employee)] = self.__model.NewBoolVar('shift_{}_employee_{}'.format(shift.name, employee.name))

    

        # ------------------------ Constraints -> Rules ---------------------------
        constraints = {}
        objectives = {}



        # Each shift must be assigned to employees more than or equal to min_employees, and less than or equal to max_employees
        for shift in self.shifts:
            constraints[f'shift_{shift.name}_min_employees'] = self.__model.NewBoolVar(f'shift_{shift.name}_min_employees_constraints')
            self.__model.Add(sum(self.__shift_vars[(shift, employee)] for employee in self.employees) >= shift.min_employees).OnlyEnforceIf(constraints[f'shift_{shift.name}_min_employees']) # type: ignore
            self.__model.Add(sum(self.__shift_vars[(shift, employee)] for employee in self.employees) <= shift.max_employees) # type: ignore

        # If the shift is assigned to employees, fixed the shift assigned to the employees
        fixed_shifts = [] # List of tuples (shift, employee)
        for shift in self.shifts:
            for employee in shift.employees:
                fixed_shifts.append((shift, employee))
        for shift, employee in fixed_shifts:
            self.__model.Add(self.__shift_vars[(shift, employee)] == 1)


        # The shift should only be assigned to the employees who are available (Compare to employee's tasks)
        for date in self.dates:
            constraints[f'employee_availability_{date.date()}'] = self.__model.NewBoolVar(f'employee_availability_constraints_{date.date()}')
            for shift in self.get_shifts_by_date(date):
                for employee in self.employees:
                    if not employee.is_available(shift) and (shift, employee) not in fixed_shifts:
                        self.__model.Add(self.__shift_vars[(shift, employee)] == 0)
                        # self.__model.Add(self.__shift_vars[(shift, employee)] == 0).OnlyEnforceIf(constraints[f'employee_availability_{date.date()}']) # type: ignore
                    if not employee.is_available(shift) and (shift, employee) in fixed_shifts:
                        print(f'Warning: {employee.first_name} is not available for {shift.name} but is assigned to it.')


        # Logical matrix for 2 shift types in the same day that cannot be assigned to the same employee in the same day
        # constraints['shift_types_matrix'] = self.__model.NewBoolVar('shift_types_logical_matrix_constraints')


        # shift_types_matrix = {
        #     'labels' : ['s1', 's1+', 'mc', 's2', 's2+', 'observe', 'ems', 'amd', 'avd'],
        #     'matrix': [
        #       # s1 s1+ mc s2 s2+ ob em amd avd
        #         [0, 0, 0, 0, 0, 0, 0, 1, 0], # s1
        #         [0, 0, 0, 0, 0, 1, 1, 1, 1], # s1+
        #         [0, 0, 0, 1, 1, 0, 0, 1, 1], # mc
        #         [0, 0, 1, 0, 0, 0, 0, 1, 0], # s2
        #         [0, 0, 1, 0, 0, 1, 1, 1, 1], # s2+
        #         [0, 1, 0, 0, 1, 0, 0, 1, 1], # ob
        #         [0, 1, 0, 0, 1, 0, 0, 1, 1], # em
        #         [1, 1, 1, 1, 1, 1, 1, 0, 1], # amd
        #         [0, 1, 1, 0, 1, 1, 1, 1, 0]  # avd
        #     ]
        # }

        # shift_labels = shift_types_matrix['labels']
        # matrix = shift_types_matrix['matrix']

        # for date in [d for d in self.dates if d.day < 16]:
        #     # constraints[f'shift_types_matrix_{date.date()}'] = self.__model.NewBoolVar(f'shift_types_matrix_constraints_{date.date()}')
        #     shifts = self.get_shifts_by_date(date)
        #     for shift1 in shifts:
        #         for shift2 in shifts:
        #             if shift1 != shift2 and shift1.type in shift_labels and shift2.type in shift_labels:
        #                 i = shift_labels.index(shift1.type)
        #                 j = shift_labels.index(shift2.type)
        #                 if not matrix[i][j]:
        #                     constraints[f'shift_types_matrix_{date.date()}_{shift1.type}_{shift2.type}'] = self.__model.NewBoolVar(f'shift_types_matrix_constraints_{date.date()}_{shift1.type}_{shift2.type}')
        #                     # print(f'{shift1.name} and {shift2.name} cannot be assigned to the same employee in the same day.')
        #                     for employee in self.employees:
        #                         # self.__model.Add(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1)
        #                         self.__model.Add(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1).OnlyEnforceIf(constraints[f'shift_types_matrix_{date.date()}_{shift1.type}_{shift2.type}']) # type: ignore

        # shift_types_matrix = {
        #     'labels' : ['s1', 's1+', 'mc', 's2', 's2+', 'observe', 'ems', 'amd', 'avd'],
        #     'matrix': [
        #       # s1 s1+ mc s2 s2+ ob em amd avd
        #         [0, 0, 0, 0, 0, 0, 0, 1, 0], # s1
        #         [0, 0, 0, 0, 0, 1, 1, 1, 1], # s1+
        #         [0, 0, 0, 1, 1, 0, 0, 1, 1], # mc
        #         [0, 0, 1, 0, 0, 0, 0, 1, 0], # s2
        #         [0, 0, 1, 0, 0, 1, 1, 1, 1], # s2+
        #         [0, 1, 0, 0, 1, 0, 0, 1, 1], # ob
        #         [0, 1, 0, 0, 1, 0, 0, 1, 1], # em
        #         [1, 1, 1, 1, 1, 1, 1, 0, 0], # amd
        #         [0, 1, 1, 0, 1, 1, 1, 0, 0]  # avd
        #     ]
        # }

        # shift_labels = shift_types_matrix['labels']
        # matrix = shift_types_matrix['matrix']

        # for date in [d for d in self.dates if d.day >= 16]:
        #     # constraints[f'shift_types_matrix2_{date.date()}'] = self.__model.NewBoolVar(f'shift_types_matrix_constraints2_{date.date()}')
        #     shifts = self.get_shifts_by_date(date)
        #     for shift1 in shifts:
        #         for shift2 in shifts:
        #             if shift1 != shift2 and shift1.type in shift_labels and shift2.type in shift_labels:
        #                 i = shift_labels.index(shift1.type)
        #                 j = shift_labels.index(shift2.type)
        #                 if not matrix[i][j]:
        #                     # print(f'{shift1.name} and {shift2.name} cannot be assigned to the same employee in the same day.')
        #                     constraints[f'shift_types_matrix_{date.date()}_{shift1.type}_{shift2.type}'] = self.__model.NewBoolVar(f'shift_types_matrix_constraints_{date.date()}_{shift1.type}_{shift2.type}')
        #                     for employee in self.employees:
        #                         # self.__model.Add(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1)
        #                         self.__model.Add(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1).OnlyEnforceIf(constraints[f'shift_types_matrix_{date.date()}_{shift1.type}_{shift2.type}']) # type: ignore


        # # Minimum and maximum shifts per employee per schedule per shift type
        # for employee in self.employees:
        #     for shift_type in [s for s in self.shift_types if s not in ['ems', 'observe']]:
        #         # constraints[f'max_shifts_per_employee_{employee.first_name}_{shift_type}'] = self.__model.NewBoolVar(f'max_shifts_per_employee_{employee.first_name}_{shift_type}_constraints')
        #         # constraints[f'min_shifts_per_employee_{employee.first_name}_{shift_type}'] = self.__model.NewBoolVar(f'min_shifts_per_employee_{employee.first_name}_{shift_type}_constraints')
        #         shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type == shift_type]

        #         # self.__model.Add(sum(shifts) <= self.shift_per_employee(shift_type, type = 'max')+2)
        #         # self.__model.Add(sum(shifts) >= self.shift_per_employee(shift_type, type = 'min'))
            
        #         # self.__model.Add(sum(shifts) <= self.shift_per_employee(shift_type, type = 'max')).OnlyEnforceIf(constraints[f'max_shifts_per_employee_{employee.first_name}_{shift_type}']) # type: ignore
        #         # self.__model.Add(sum(shifts) >= self.shift_per_employee(shift_type, type = 'min')).OnlyEnforceIf(constraints[f'min_shifts_per_employee_{employee.first_name}_{shift_type}']) # type: ignore
                


        # # Minimum and maximum shifts per employee per schedule for all shift types
        # constraints['min_shifts_per_employee_all'] = self.__model.NewBoolVar('min_shifts_per_employee_all_constraints')
        # constraints['max_shifts_per_employee_all'] = self.__model.NewBoolVar('max_shifts_per_employee_all_constraints')
        # for employee in self.employees:
        #     shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts]
        #     shifts_per_employee = len(self.shifts) / len(self.employees)
        #     self.__model.Add(sum(shifts) <= math.floor(shifts_per_employee)+1).OnlyEnforceIf(constraints['max_shifts_per_employee_all']) # type: ignore
        #     self.__model.Add(sum(shifts) >= math.floor(shifts_per_employee)).OnlyEnforceIf(constraints['min_shifts_per_employee_all']) # type: ignore
        #     # TODO: In case of failure, change to objective

        # Custom shift groups summate to a specific value per employee



        # shift_group_sum = {
        #     ('max',('mc')) : 2,
        #     ('min',('mc')) : 1,
        #     ('max',('amd')) : 2,
        #     ('min',('amd')) : 1,
        #     ('max',('avd')) : 3,
        #     ('min',('avd')) : 2,
        #     ('max',('s1', 's2')) : 4,
        #     ('min',('s1', 's2')) : 3,
        #     ('max',('s1', 's1+', 's2', 's2+')) : 7,
        #     ('min',('s1', 's1+', 's2', 's2+')) : 6,
            
        # }
        # for employee in self.employees:
        #     for group in shift_group_sum:
        #         shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in group[1]]
        #         constraints[f'shift_group_sum_max_{group[1]}_{employee.first_name}'] = self.__model.NewBoolVar(f'shift_group_sum_max_constraints_{group[1]}_{employee.first_name}')
        #         constraints[f'shift_group_sum_min_{group[1]}_{employee.first_name}'] = self.__model.NewBoolVar(f'shift_group_sum_min_constraints_{group[1]}_{employee.first_name}')
        #         # print(f'{employee.first_name} {shifts}')
        #         if group[0] == 'max':
        #             self.__model.Add(sum(shifts) <= shift_group_sum[group]).OnlyEnforceIf(constraints[f'shift_group_sum_max_{group[1]}_{employee.first_name}']) # type: ignore
        #             # self.__model.Add(sum(shifts) <= shift_group_sum[group]).OnlyEnforceIf(constraints['shift_group_sum_max']) # type: ignore
        #         elif group[0] == 'min':
        #             # self.__model.Add(sum(shifts) >= shift_group_sum[group])
        #             self.__model.Add(sum(shifts) >= shift_group_sum[group]).OnlyEnforceIf(constraints[f'shift_group_sum_min_{group[1]}_{employee.first_name}']) # type: ignore


        # #AVD
        # for employee in self.employees:
        #     constraints[f'avd_max_{employee.first_name}'] = self.__model.NewBoolVar(f'avd_constraints_{employee.first_name}')
        #     constraints[f'avd_min_{employee.first_name}'] = self.__model.NewBoolVar(f'avd_constraints_{employee.first_name}')
        #     # shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['avd'] and shift.day <16]
        #     # self.__model.Add(sum(shifts) <= 2)
        #     # self.__model.Add(sum(shifts) >= 1)
        #     shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['avd'] and shift.day >=16]
        #     self.__model.Add(sum(shifts) <= 2).OnlyEnforceIf(constraints[f'avd_max_{employee.first_name}']) # type: ignore
        #     self.__model.Add(sum(shifts) >= 1).OnlyEnforceIf(constraints[f'avd_min_{employee.first_name}']) # type: ignore

        # #Holiday
        # for employee in self.employees:
        #     constraints[f'holiday_max_{employee.first_name}'] = self.__model.NewBoolVar(f'holiday_constraints_{employee.first_name}')
        #     constraints[f'holiday_min_{employee.first_name}'] = self.__model.NewBoolVar(f'holiday_constraints_{employee.first_name}')
        #     shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date in self.holiday_dates]
        #     # print(f'{employee.first_name} - {shifts}')
        #     self.__model.Add(sum(shifts) <= 2).OnlyEnforceIf(constraints[f'holiday_max_{employee.first_name}']) # type: ignore
        #     self.__model.Add(sum(shifts) >= 1).OnlyEnforceIf(constraints[f'holiday_min_{employee.first_name}']) # type: ignore



        # # TODO: Discuss กับ อจก ว่ายังอยากให้มี constraint นี้ไหม
        # shift_group_sum_employee = {
        #     ('s1', 's2', 's1+', 's2+'): self.__shift_group_sum_employee,
        #     ('s1','s2'): {
        #     # 'BC': 2,
        #     # 'BW': 3,
        #     # 'KS': 3,
        #     # 'PT': 3,
        #     # 'PL':1,
        #     # 'BT': 3,
        #     # 'BK': 3,
        #     # 'CC': 3,
        #     # 'KL': 3,
        #     # 'PU': 3,
        #     # 'NM': 3,
        #     # 'SS': 0,
        #     # 'UT': 3,
        #     },
        #     ('s1+','s2+'): {
        #     # 'BC': 7,
        #     # 'BW': 5,
        #     # 'KS': 6,
        #     # 'PT': 5,
        #     # 'PL': 3,
        #     # 'BT': 5,
        #     # 'BK': 6,
        #     # 'CC': 7,
        #     # 'KL': 5,
        #     # 'PU': 6,
        #     # 'NM': 5,
        #     # 'SS': 6,
        #     },
        #     }
        
        # for group in shift_group_sum_employee:
        #     for e in shift_group_sum_employee[group]:
                
        #         # select employee by abbreviation
        #         employee = [employee for employee in self.employees if employee.abbreviation == e][0]
        #         constraints[f'shift_group_sum_employee_{employee.first_name}_{group}'] = self.__model.NewBoolVar(f'shift_group_sum_employee_{employee.first_name}_{group}_constraints')
        #         shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in group]

        #         # self.__model.Add(sum(shifts) == shift_group_sum_employee[group][e])
        #         self.__model.Add(sum(shifts) == shift_group_sum_employee[group][e]).OnlyEnforceIf(constraints[f'shift_group_sum_employee_{employee.first_name}_{group}']) # type: ignore

     
        

        # ------------------------ Objective ---------------------------
        objective_names = []
        obj_bool_vars = []
        obj_bool_coeffs = []
        obj_int_vars = []
        obj_int_coeffs = []

        # Minimize the number of shifts assigned to the same employee in the same day
        ls_vars = []
        ls_coeff = []
        objective_names.append('Minimize the number of shifts assigned to the same employee in the same day')
        for day in self.days:
            # num_available_employee = len([e for e in self.employees if e.is_available_date(day)])
            # num_shifts = len([s for s in self.shifts if s.start_time.date() == day])
            for employee in self.employees:
                constraints[f'max_shifts_per_day_{day}_{employee.first_name}'] = self.__model.NewBoolVar(f'max_shifts_per_day_constraints_{day}_{employee.first_name}')
                objectives[f'max_shifts_per_day_{day}_{employee.first_name}'] = self.__model.NewBoolVar(f'max_shifts_per_day_objective_{day}_{employee.first_name}')
                # objectives[f'max2_shifts_per_day_{day}_{employee.first_name}'] = self.__model.NewBoolVar(f'max2_shifts_per_day_objective_{day}_{employee.first_name}')
                shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.start_time.date() == day]
                
                self.__model.Add(sum(shifts)<=1).OnlyEnforceIf(objectives[f'max_shifts_per_day_{day}_{employee.first_name}']) # Soft constraint  # type: ignore
                self.__model.Add(sum(shifts)<=2).OnlyEnforceIf(constraints[f'max_shifts_per_day_{day}_{employee.first_name}']) # Soft constraint  # type: ignore
                
                ls_vars.append(objectives[f'max_shifts_per_day_{day}_{employee.first_name}'])
                ls_coeff.append(1)
                # print(f'{day} - {employee.name} - {sum(shifts)}')
        obj_bool_vars.append(ls_vars)
        obj_bool_coeffs.append(ls_coeff)

        # # Maximize distance between 2 adjacented shifts as much as possible (int version)
        # ls_vars = []
        # ls_coeff = []
        # objective_names.append('Maximize distance between 2 adjacented shifts as much as possible (int version)')
        # for shift_type in self.shift_types:
        #     for employee in self.employees:
        #         shifts = [shift for shift in self.shifts if shift.shift_type == shift_type]
        #         for shift1 in shifts:
        #             for shift2 in [shift for shift in shifts if shift != shift1 and shift.start_time > shift1.start_time]:
        #                 objectives[f'shift_distance_delta_{shift1}_{shift2}'] = self.__model.NewIntVar(0, 100, f'maximize_distance_between_shifts_{shift_type}')
        #                 bool_var = self.__model.NewBoolVar(f'maximize_distance_between_shifts_{shift1}_{shift2}')
        #                 delta = abs(shift1.start_time - shift2.start_time).days
        #                 # bool_var represents the condition that shift1 and shift2 are assigned to the same employee 
        #                 self.__model.Add(self.__shift_vars[(shift1, employee)] == self.__shift_vars[(shift2, employee)]).OnlyEnforceIf(bool_var) # type: ignore
        #                 self.__model.Add(sum([self.__shift_vars[(shift1, employee)], self.__shift_vars[(shift2, employee)]]) <= 1).OnlyEnforceIf(bool_var.Not()) # type: ignore
        #                 self.__model.Add(objectives[f'shift_distance_delta_{shift1}_{shift2}'] == delta).OnlyEnforceIf(bool_var) # type: ignore
        #                 ls_vars.append(objectives[f'shift_distance_delta_{shift1}_{shift2}'])
        #                 ls_coeff.append(1)
        # obj_int_vars.append(ls_vars)
        # obj_int_coeffs.append(ls_coeff)


        # #Holiday
        # ls_vars = []
        # ls_coeff = []
        # objective_names.append('Average number of shifts per employee on holiday')
        # for employee in self.employees:
        #     objectives[f'holiday_{employee.first_name}'] = self.__model.NewIntVar(0, 100, f'holiday_{employee.first_name}')
        #     shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date in self.holiday_dates]
        #     holiday_average = math.ceil(len(shifts) / len(self.employees))
        #     delta = self.__model.NewIntVar(0, 100, f'holiday_delta_{employee.first_name}')
        #     self.__model.AddAbsEquality(delta, sum(shifts) - holiday_average)
        #     self.__model.Add(objectives[f'holiday_{employee.first_name}'] == delta)
        #     ls_vars.append(objectives[f'holiday_{employee.first_name}'])
        #     ls_coeff.append(-1)

        #     # shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date in self.holiday_dates]
        #     # num_shifts = sum(shifts)
        #     # self.__model.Add(objectives[f'holiday_{employee.first_name}'] == num_shifts)
        #     # ls_vars.append(objectives[f'holiday_{employee.first_name}'])
        #     # ls_coeff.append(-1)

        # obj_int_vars.append(ls_vars)
        # obj_int_coeffs.append(ls_coeff)    


        # TODO: Re-open this objective
        # # Maximize distance between 2 adjacented shifts as much as possible (int version)
        # ls_vars = []
        # ls_coeff = []
        # objective_names.append('Maximize distance between 2 adjacented shifts (shift group) as much as possible (int version)')
        # shift_groups = [
        #     ['s1', 's1+', 's2', 's2+'],
        #     ['mc'],
        #     ['amd', 'avd'],
        #     # ['avd']
        # ]

        # for group in shift_groups:
        #     for employee in self.employees:
        #         shifts = [shift for shift in self.shifts if shift.shift_type in group]
        #         for shift1 in shifts:
        #             for shift2 in [shift for shift in shifts if shift != shift1 and shift.start_time > shift1.start_time]:
        #                 # Date interval between 2 shifts
        #                 date_interval = [date for date in self.dates if shift1.start_time <= date <= shift2.start_time]
        #                 # other_shifts = [shift for shift in self.shifts if shift.date in date_interval and shift != shift1 and shift != shift2]
                        
        #                 delta = abs(shift1.start_time - shift2.start_time).days
        #                 objectives[f'shift_distance_delta_{shift1}_{shift2}'] = self.__model.NewIntVar(0, 100, f'maximize_distance_between_shifts_{shift1}_{shift2}')
        #                 bool_var = self.__model.NewBoolVar(f'maximize_distance_between_shifts_{shift1}_{shift2}')
                        
        #                 # bool_var represents the condition that shift1 and shift2 are assigned to the same employee 
        #                 self.__model.Add(self.__shift_vars[(shift1, employee)] == self.__shift_vars[(shift2, employee)]).OnlyEnforceIf(bool_var) # type: ignore
        #                 self.__model.Add(sum([self.__shift_vars[(shift1, employee)], self.__shift_vars[(shift2, employee)]]) <= 1).OnlyEnforceIf(bool_var.Not()) # type: ignore
                        
        #                 self.__model.Add(objectives[f'shift_distance_delta_{shift1}_{shift2}'] == delta).OnlyEnforceIf(bool_var) # type: ignore
        #                 ls_vars.append(objectives[f'shift_distance_delta_{shift1}_{shift2}'])
        #                 ls_coeff.append(1)
        # obj_int_vars.append(ls_vars)
        # obj_int_coeffs.append(ls_coeff)

    
        # Avoid working with thse shift in the same group on consecutive days
        ls_vars = []
        ls_coeff = []
        objective_names.append('Avoid working with thse shift in the same group on consecutive days')
        shift_groups = [
            ['s1', 's1+', 's2', 's2+'],
            ['mc'],
            ['amd', 'avd'],
            ['avd']
        ]

        for group in shift_groups:
            for employee in self.employees:
                shifts = [shift for shift in self.shifts if shift.shift_type in group]
                for shift1 in shifts:
                    for shift2 in [shift for shift in shifts if shift != shift1 and shift.start_time > shift1.start_time and shift.start_time - shift1.start_time <= timedelta(days=1)]:
                        
                        bool_var = self.__model.NewBoolVar(f'avoid_consecutive_days_{shift1}_{shift2}')
                        self.__model.Add(sum([self.__shift_vars[(shift1, employee)], self.__shift_vars[(shift2, employee)]])<=1).OnlyEnforceIf(bool_var) # type: ignore
                        self.__model.Add(self.__shift_vars[(shift1, employee)] == self.__shift_vars[(shift2, employee)]).OnlyEnforceIf(bool_var.Not()) # type: ignore
                        ls_vars.append(bool_var)
                        ls_coeff.append(1)
        obj_bool_vars.append(ls_vars)
        obj_bool_coeffs.append(ls_coeff)
                        
        # Shift preference (Some staff want to work S2/S2+ more than S1/S1+)
        ls_vars = []
        ls_coeff = []
        objective_names.append('Shift preference (Some staff want to work S2/S2+ more than S1/S1+)')
        # shift_preference = {
        #     'BC' : 'morning',
        #     'BW' : 'morning',
        #     'KS' : 'morning',
        #     'PT' : 'morning',
        #     'BK' : None,
        #     'CC' : None,
        #     'KL' : None,
        #     'PU' : None,
        #     'NM' : 'afternoon',
        #     'SS' : 'afternoon',
        #     'UT' : 'afternoon',
        #     'KB' : 'morning',
        # }

        shift_preference = self.__shift_preference

        print(shift_preference)


        for employee in self.employees:
            for shift in self.shifts:
                if shift_preference[employee.abbreviation] == 'morning' and shift.type in ['s1', 's1+']:
                    self.__model.Add(self.__shift_vars[(shift, employee)] == 0)
                elif shift_preference[employee.abbreviation] == 'afternoon' and shift.type in ['s2', 's2+']:
                    self.__model.Add(self.__shift_vars[(shift, employee)] == 0)

               
        obj_bool_vars.append(ls_vars)
        obj_bool_coeffs.append(ls_coeff)
    


                

        # # Equalize work load between employees
        # ls_vars = []
        # ls_coeff = []
        # objective_names.append('Equalize work load between employees')
        # for employee in self.employees:
        #     if employee.role == 'unassigned':
        #         continue
        #     for shift_type in self.shift_types:
        #         workload_per_staff = self.__model.NewIntVar(0, 1000, f'Workload of {employee.first_name} for {shift_type}')
        #         self.__model.Add(sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.shift_type == shift_type] ) == workload_per_staff)
        #         for employee2 in self.employees:
        #             if employee2 == employee:
        #                 continue
        #             workload_per_staff2 = self.__model.NewIntVar(0, 1000, f'Workload of {employee2.first_name} for {shift_type}')
        #             self.__model.Add(sum([self.__shift_vars[(shift, employee2)] for shift in self.shifts if shift.shift_type == shift_type] ) == workload_per_staff2)
        #             delta = self.__model.NewIntVar(0, 1000, f'Delta of {employee.first_name} and {employee2.first_name} for {shift_type}')
        #             self.__model.AddAbsEquality(delta, workload_per_staff - workload_per_staff2)
        #             ls_vars.append(delta)
        #             ls_coeff.append(1)

        # obj_int_vars.append(ls_vars)
        # obj_int_coeffs.append(ls_coeff)
                            




        const_penalties = sum([constraint for constraint in constraints.values()]) 
        const_penalties_var = self.__model.NewIntVar(-10000, 10000, 'const_penalties')
        self.__model.Add(const_penalties_var == const_penalties)
        self.__model.Maximize(const_penalties_var)

        # obj_bool_penalties = sum([coeff * vars for coeff, vars in zip(obj_bool_coeffs, obj_bool_vars)])
        # obj_int_penalties = sum([coeff * vars for coeff, vars in zip(obj_int_coeffs, obj_int_vars)])
        # self.__penalties = obj_bool_penalties + obj_int_penalties + const_penalties

        # Grouped penalties for each objective and try to satisfy one objective at a time
        ls_penalties = []
        for ls_vars, ls_coeff in zip(obj_bool_vars, obj_bool_coeffs):
            penalties = sum([coeff * vars for coeff, vars in zip(ls_coeff, ls_vars)])
            # print(ls_vars)
            penalties_var_bool = self.__model.NewIntVar(-10000, 10000, 'penalties')
            self.__model.Add(penalties_var_bool == penalties)
            ls_penalties.append(penalties_var_bool)
            # print(ls_penalties)
        
        for ls_vars, ls_coeff in zip(obj_int_vars, obj_int_coeffs):
            # penalties = sum([coeff * vars for coeff, vars in zip(ls_coeff, ls_vars)])
            penalties_var_int = self.__model.NewIntVar(-100000000, 100000000, 'penalties')
            self.__model.Add(cp_model.LinearExpr.WeightedSum(ls_vars, ls_coeff) == penalties_var_int)
            # self.__model.Add(penalties_var == penalties)
            ls_penalties.append(penalties_var_int)
            # print(ls_vars)
        
        # print(ls_penalties)


        # ------------------------ Solver ---------------------------

        # add assumptions
        # self.__model.AddAssumptions([constraint for constraint in constraints.values()])


        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8

        # Solve model - satisfy only constraints
        print(f'Begin solving with constraints')
        status = solver.Solve(self.__model)

        # print the number of constraints that are not satisfied
        try:
            print(f'Constraints satisfaction: {solver.Value(const_penalties_var)} ({solver.Value(const_penalties_var) / len(constraints) * 100 :.2f} %)')
        except Exception as e:
            print(e)

        # Save constraint satisfaction
        self.__model.Add(const_penalties_var >= round(solver.ObjectiveValue()))

        # ----------------- Complete the objectives ------------------
        for penalties in ls_penalties:

            self.__model.Maximize(penalties)
            print(f'Begin solving with objective {objective_names[ls_penalties.index(penalties)]}')
            status = solver.Solve(self.__model)
            # Save objective satisfaction
            self.__model.Add(penalties >= round(solver.ObjectiveValue()))
            try:
                # print(penalties)
                print(f'Objective satisfaction: {solver.ObjectiveValue()}')
            except Exception as e:
                print(e)
             


        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # if verbose:
            print('Solution:')
            # print('Objective value =', solver.ObjectiveValue())
            for shift in self.shifts:
                for employee in self.employees:
                    if solver.Value(self.__shift_vars[(shift, employee)]) == 1:
                        # print(f'{shift.name} is assigned to {employee.name}')
                        try:
                            shift.add_employee(employee)
                            employee.add_task(shift)
                        except Exception as e:
                            pass
            for constraint in constraints:
                if solver.Value(constraints[constraint]) == 0:
                    print(f'{constraint} is not satisfied')
            #     print(f'{constraint}: {solver.BooleanValue(constraints[constraint])}')

            # for objective in objectives:
            #     print(f'{objective}: {solver.BooleanValue(objectives[objective])}')

            # Give a warning if the employee is assigned to 2 shift types in the same day that cannot be assigned to the same employee in the same day
            # for employee in self.employees:
            #     for shift1 in [shift for shift in self.shifts if shift not in fixed_shifts]:
            #         for shift2 in [shift for shift in self.shifts if shift != shift1 and shift.start_time.date() == shift1.start_time.date() and shift not in fixed_shifts]:
            #             i = shift_labels.index(shift1.shift_type)
            #             j = shift_labels.index(shift2.shift_type)
            #             if not matrix[i][j]:
            #                 if solver.Value(self.__shift_vars[(shift1, employee)]) == 1 and solver.Value(self.__shift_vars[(shift2, employee)]) == 1:
            #                     print(f'Warning: {employee.name} is assigned to {shift1.name} and {shift2.name} in the same day.')
            return True
        else:
            print('No solution found.')
            # for constraint in constraints:
            #     print(f'{constraint}: {solver.BooleanValue(constraints[constraint])}')
                
            # print(f'{solver.SufficientAssumptionsForInfeasibility()}')
            return False

    def to_matrix(self):
        """Convert the schedule to a matrix of employee assign to shift"""

        dates = [date.date() for date in pd.date_range(self.start_time, self.end_time, freq='D')]
        shifts = self.shifts
        shift_types = self.shift_types
        employees = self.employees
        
        shift_schedule = pd.DataFrame(index=dates, columns=[shift_type for shift_type in shift_types])
        shift_by_type = {}
        # Optimized version
        for shift in shifts:
            if shift.shift_type in shift_by_type:
                shift_by_type[shift.shift_type].append(shift)
            else:
                shift_by_type[shift.shift_type] = [shift]

        # Fill the dataframe with the employees assigned to each shift, if no shift is assigned, fill with 'Unassigned'
        for date in dates:
            for shift_type in shift_by_type:
                for shift in shift_by_type[shift_type]:
                    if shift.start_time.date() == date:
                        if len(shift.employees) == 0:
                            shift_schedule.loc[date, shift_type] = 'Unassigned'
                        elif len(shift.employees) == 1:
                            shift_schedule.loc[date, shift_type] = shift.employees[0].abbreviation
                        elif len(shift.employees) > 1:
                            shift_schedule.loc[date, shift_type] = str([employee.abbreviation for employee in shift.employees])
        
        # Fill nan values with '' (empty string)
        shift_schedule = shift_schedule.fillna('')

        # Reorder the columns
        columns = ['mc', 's1', 's1+', 's2', 's2+', 'ems', 'observe', 'amd', 'avd']
        shift_schedule = shift_schedule[columns].values.tolist()

        return shift_schedule
    

    # console command line to export requirement.txt with conda
    # conda list -e > requirements.txt
    
    # provide a list of string logs to the user for debugging
    def logging(self):
        """provide a list of string logs to the user for debugging"""
        logs = []
        # Basic information
        logs.append(f'Basic information:')
        logs.append(f'Number of employees: {len(self.employees)}')
        logs.append(f'Number of shifts: {len(self.shifts)}')
        logs.append(f'Number of shift types: {len(self.shift_types)}')
        logs.append(f'Number of days: {len(self.days)}')
        logs.append(f'Number of holiday dates: {len(self.holiday_dates)}')
        logs.append(f'')

        logs.append(f'Programming logs:')       
        logs = logs + self.__logs

        return logs

