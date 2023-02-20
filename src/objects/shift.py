import datetime
from timeinterval import TimeInterval, TimeIntervals
from employee import Employee


class Shift:
    def __init__(self, interval: TimeInterval, min_employees: int = 1, max_employees: int = 1, shift_name: str = None, shift_type: str = None, workload_coefficient: int = 1):
        assert min_employees <= max_employees, "Minimum number of employees cannot be greater than maximum number of employees"
        self.interval = interval
        self.min_employees = min_employees
        self.max_employees = max_employees
        self.assigned_employees = []
        self.num_assigned_employees = 0
        self.shift_name = shift_name
        self.shift_type = shift_type
        self.workload_coefficient = workload_coefficient
        self.start_time = self.interval.start_time
        self.end_time = self.interval.end_time
        self.duration = self.interval.duration()

        if self.shift_name is None:
            self.shift_name = self.interval.get_start_time().strftime("%H:%M") + " - " + self.interval.get_end_time().strftime("%H:%M")

    def __str__(self):
        return self.shift_name

    def __repr__(self):
        return str(self)

    def add_assigned_employee(self, employee: Employee):
        # check if the employee is already assigned to the shift
        if employee in self.assigned_employees:
            raise Exception("Employee is already assigned to this shift")
        # check if the shift is full
        if self.num_assigned_employees == self.max_employees:
            raise Exception("Shift is full")

        self.assigned_employees.append(employee)
        self.num_assigned_employees += 1

        #update the employee's availability
        employee.availability = employee.availability - self.interval 

    def remove_assigned_employee(self, employee: Employee):
        # check if the employee is assigned to the shift
        if employee not in self.assigned_employees:
            raise Exception("Employee is not assigned to this shift")

        self.assigned_employees.remove(employee)
        self.num_assigned_employees -= 1

    def add_assigned_employees(self, employees: list):
        # check if the shift is full
        if self.num_assigned_employees + len(employees) > self.max_employees:
            raise Exception("Exceeds maximum number of employees for this shift")

        # add if the employee is not already assigned to the shift
        for employee in employees:
            if employee not in self.assigned_employees:
                self.assigned_employees.append(employee)
                self.num_assigned_employees += 1
    
    def reset_employees(self):
        self.assigned_employees = []
        self.num_assigned_employees = 0

    def change_shift_type(self, shift_type: str):
        self.shift_type = shift_type

    def change_workload_coefficient(self, workload_coefficient: int):
        self.workload_coefficient = workload_coefficient

    def change_min_employees(self, min_employees: int):
        self.min_employees = min_employees

    def change_max_employees(self, max_employees: int):
        self.max_employees = max_employees

    def change_shift_name(self, shift_name: str):
        self.shift_name = shift_name

    def change_interval(self, interval: TimeInterval):
        self.interval = interval
        self.start_time = self.interval.start_time
        self.end_time = self.interval.end_time
        self.duration = self.interval.duration()

