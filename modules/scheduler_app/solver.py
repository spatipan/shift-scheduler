from datetime import datetime, timedelta
from .models.models import *
from ortools.sat.python import cp_model
import logging
import math

# Constraint object - constraint, status
class SchedulerConstraint:
    def __init__(self, model, constraint, group: str, status: str, *args, **kwargs):
        self.model = model
        self.constraint = constraint
        self.group = group
        self.status = status
        self.args = args
        self.kwargs = kwargs


# Constraint group object - constraints, status

class SchedulerConstraintGroup:
    def __init__(self, title: str, constraints: list, status: str):
        self.title = title
        self.constraints = constraints
        self.status = status
    
# Schedule solver
class ScheduleSolver:
    def __init__(self):
        self.schedule = None

        self.model = None # Initialize model - gurobi, ortools, etc
        self.status = '' # unsolved, infeasible, feasiblem optimal
        self.solutions = []

        self.__model = cp_model.CpModel()
        self.__shift_vars = {}
        self.__penalties = 0

        self.logger = logging.getLogger(__class__.__name__)

        # Constraint
        self.__shift_group_sum_employee = {}
        self.__shift_sum_employee = {}

        # Objective
        self.__shift_preference = {}

    @property
    def shifts(self):
        return self.schedule.shifts if self.schedule else []
    
    @property
    def employees(self):
        return self.schedule.employees if self.schedule else []
    
    @property
    def dates(self):
        return self.schedule.dates if self.schedule else []
    
    @property
    def days(self):
        return self.schedule.days if self.schedule else []
    
    @property
    def holiday_dates(self):
        return self.schedule.holiday_dates if self.schedule else []
    
    @property
    def work_dates(self):
        return [date for date in self.dates if date not in self.holiday_dates]
    
    @property
    def work_days(self):
        return [date.date() for date in self.work_dates]
    
    @property
    def shift_types(self):
        return self.schedule.shift_types if self.schedule else []
    
    def shift_per_employee(self, shift_type: str, requirement = []) -> float:
        # average = sum([shift.shift_type == shift_type for shift in self.shifts]) / len(self.employees)
        # return average
        if requirement == []:
            eligible_employees = self.employees
        else:
            eligible_employees = [employee for employee in self.employees if employee.skills in requirement]
        average = sum([shift.type == shift_type for shift in self.shifts]) / len(eligible_employees)
        return average

    def get_shifts_by_date(self, date: datetime) -> list[Shift]:
        return self.schedule.get_shifts_by_date(date) if self.schedule else []

    def add_total_shifts_constraint(self, employee_abbreviation: str, total_shifts: int):
        '''Add total shifts constraint'''
        self.__shift_group_sum_employee[employee_abbreviation] = total_shifts
        self.logger.debug(f'Added total shifts constraint for {employee_abbreviation} - {total_shifts}')

    def add_total_shifts_per_employee_constraint(self):
        '''Add total shifts per employee constraint'''
        pass

    def add_shift_preference_constraint(self, employee_abbreviation: str, morning_preference: bool, afternoon_preference: bool):
        '''Add shift preference constraint'''
        if morning_preference:
            self.__shift_preference[employee_abbreviation] = 'morning'
        elif afternoon_preference:
            self.__shift_preference[employee_abbreviation] = 'afternoon'
        else:
            self.__shift_preference[employee_abbreviation] = None
        # print(self.__shift_preference)
        self.logger.debug(f'Added shift preference constraint for {employee_abbreviation} - morning: {morning_preference}, afternoon: {afternoon_preference}')

    def visualize(self):
        '''Visualize schedule using matplotlib, plotly, etc.'''
        pass
        # visualize schedule

    def check_feasibility(self):
        pass
        # solve only constraint group by group
    
    def solve(self, schedule: Schedule | None = None):
        '''Solve the schedule'''
        assert schedule is not None, 'Schedule is not defined'
        self.schedule = schedule

        # ------------------------ Variable ---------------------------
        self.__shift_vars = {}
        for shift in self.shifts:
            for employee in self.employees:
                self.__shift_vars[(shift, employee)] = self.__model.NewBoolVar('shift_{}_employee_{}'.format(shift.title, employee.abbreviation)) #

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
        # print("Fix:", ls_fixed_shifts)
            
        ls_not_fixed_shifts = [shift for shift in self.shifts if shift not in ls_fixed_shifts]
        # print("Not fix:", ls_not_fixed_shifts)

        # [3] The shift should only be assigned to the employees who are available (Compare to employee's tasks), except for fixed shifts
        
        for date in self.dates:
            for shift in self.get_shifts_by_date(date):
                for employee in self.employees:
                    if not employee.is_available(shift) and (shift, employee) not in fixed_shifts:
                        date_constraints[shift.date].append(self.__shift_vars[(shift, employee)] == 0)     
                    elif not employee.is_available(shift) and (shift, employee) in fixed_shifts:
                        self.logger.debug(f'{shift.title} is assigned to {employee.abbreviation} but they are not available on {date.date()}')
                    else:
                        continue
        

        # [4.1] Some shifts cannot be assigned to the same employee in the same day, represent with a logical matrix, exclude fixed shifts
        # TODO: Create an automatic way to feed the shift_types_matrix
        shift_types_matrix = {
                    # service night
                    ('service night', 'service1') : False,
                    ('service night', 'service2') : False,
                    ('service night', 'service1+') : False,
                    ('service night', 'service2+') : False,
                    ('service night', 'mc') : False,
                    ('service night', 'observe') : False,
                    ('service night', 'ems') : False,
                    ('service night', 'amd') : False,
                    ('service night', 'avd') : False,

                    # service1
                    ('service1', 'service2') : True,
                    ('service1', 'service1+') : False,
                    ('service1', 'service2+') : False,
                    ('service1', 'mc') : False,
                    ('service1', 'observe') : False,
                    ('service1', 'ems') : False,
                    ('service1', 'amd') : False,
                    ('service1', 'avd') : False,

                    # service2
                    ('service2', 'service1+') : False,
                    ('service2', 'service2+') : False,
                    ('service2', 'mc') : True,
                    ('service2', 'observe') : False,
                    ('service2', 'ems') : False,
                    ('service2', 'amd') : False,
                    ('service2', 'avd') : False,

                    # service1+
                    ('service1+', 'service2+') : True,
                    ('service1+', 'mc') : False,
                    ('service1+', 'observe') : True,
                    ('service1+', 'ems') : True,
                    ('service1+', 'amd') : True,
                    ('service1+', 'avd') : False,

                    # service2+
                    ('service2+', 'mc') : True,
                    ('service2+', 'observe') : True,
                    ('service2+', 'ems') : True,
                    ('service2+', 'amd') : True,
                    ('service2+', 'avd') : False,

                    # mc
                    ('mc', 'observe') : True,
                    ('mc', 'ems') : True,
                    ('mc', 'amd') : True,
                    ('mc', 'avd') : False,

                    # observe
                    ('observe', 'ems') : True,
                    ('observe', 'amd') : True,
                    ('observe', 'avd') : False,

                    # ems
                    ('ems', 'amd') : True,
                    ('ems', 'avd') : False,

                    # amd
                    ('amd', 'avd') : False,

        }

        keys = list(shift_types_matrix.keys())
        
        for date in self.dates:
            shifts = self.get_shifts_by_date(date)
            not_fix = [shift for shift in shifts if shift not in ls_fixed_shifts] # exclude fixed shifts
            
            for shift1 in shifts:
                for shift2 in not_fix:
                    if shift1 == shift2:
                        continue
                    if (shift1.type, shift2.type) in keys and shift_types_matrix[(shift1.type, shift2.type)] == False: # type: ignore
                        for employee in self.employees:
                            date_constraints[date.date()].append(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1)
                            # self.logger.debug(f'{shift1.title} and {shift2.title} cannot be assigned to the same employee {employee} on {date.date()}')
        
                  

        # [4.2] If an employee available lower than minimum number of shift, they can work s1 and s2 shifts on the same day


        # [4.3] Employee cannot work more than 2 shifts per day, unless both in fixed shifts
        for date in self.dates:
            for employee in self.employees:
                shifts = self.get_shifts_by_date(date)
                fixed = [shift for shift in shifts if shift in ls_fixed_shifts]
                if len(fixed) < 2:
                    date_constraints[date.date()].append(sum([self.__shift_vars[(shift, employee)] for shift in self.get_shifts_by_date(date)]) <= 2)
                    # self.logger.debug(f'{employee.abbreviation} cannot work more than 2 shifts on {date.date()}')
    

        #[5] Fair distribution of shifts per employee per shift type
        # TODO: Create an automatic way to feed the shift_group_sum, may be 'increment constraint with maximize the minimum'?
        shift_group_sum = {
            ('max', ('service night'), '') : math.floor(self.shift_per_employee('service night'))+4,
            # ('min', ('service night'), '') : math.floor(self.shift_per_employee('service night')),
            ('max',('service1', 'service2', 'service1+', 'service2+'),'') : math.floor(self.shift_per_employee('service1') + self.shift_per_employee('service2') + self.shift_per_employee('service1+') + self.shift_per_employee('service2+'))+2,
            ('min',('service1', 'service2', 'service1+', 'service2+'),'') : math.floor(self.shift_per_employee('service1') + self.shift_per_employee('service2') + self.shift_per_employee('service1+') + self.shift_per_employee('service2+'))-1,
            ('max',('service1', 'service2'),'') : math.floor(self.shift_per_employee('service1') + self.shift_per_employee('service2'))+2,
            ('min',('service1', 'service2'),'') : math.floor(self.shift_per_employee('service1') + self.shift_per_employee('service2'))-1,
            ('max',('service1+', 'service2+'),'') : math.floor(self.shift_per_employee('service1+') + self.shift_per_employee('service2+'))+2,
            ('min',('service1+', 'service2+'),'') : math.floor(self.shift_per_employee('service1+') + self.shift_per_employee('service2+'))-1,


            ('max',('mc'),'') : math.floor(self.shift_per_employee('mc'))+1,
            ('min',('mc'),'') : math.floor(self.shift_per_employee('mc')),
            ('max',('amd'),'') : math.floor(self.shift_per_employee('amd'))+1,
            ('min',('amd'),'') : math.floor(self.shift_per_employee('amd')),
            ('max',('avd'),'') : math.floor(self.shift_per_employee('avd'))+1,
            ('min',('avd'),'') : math.floor(self.shift_per_employee('avd')),

        }

        for employee in self.employees:
            employee_constraints[employee] = []
            for group in shift_group_sum:
                shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in group[1]]
                if group[0] == 'max':
                    employee_constraints[employee].append(sum(shifts) <= shift_group_sum[group])
                elif group[0] == 'min':
                    employee_constraints[employee].append(sum(shifts) >= shift_group_sum[group])

       
        # [ุ6] Manual set number of shifts per employee
        shift_sum_employee = self.__shift_group_sum_employee

        for e, shift_sum in shift_sum_employee.items():
            employee = [employee for employee in self.employees if employee.abbreviation == e][0]
            shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['service1', 'service2', 'service1+', 'service2+']]
            employee_constraints[employee].append(sum(shifts) == shift_sum)
            # self.logger.debug(f'shift_sum_employee: {shifts}')


        # for e, shift_type in shift_sum_employee.items():
        #     employee = [employee for employee in self.employees if employee.abbreviation == e][0]
        #     shifts = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type == shift_type]
            # if len(shifts) > 0:
            #     employee_constraints[employee].append(sum(shifts) == shift_sum_employee[e, shift_type])
            # elif shift_type == 'total services':
            #     employee_constraints[employee].append(sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['service1', 'service2', 'service1+', 'service 2+']]) == shift_sum_employee[e, shift_type])
            # self.logger.debug(f'{e} - {shift_type} - {shift_sum_employee[e, shift_type]}')


        # [7] Some shift required a role of employee
        # for shift in self.shifts:
        #     if shift.type in ['specialist']:
        #         for employee in self.employees:
        #             if employee.skills != 'specialist':
        #                 date_constraints[shift.date].append(self.__shift_vars[(shift, employee)] == 0)


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
        
        # [1] Prefer working service1, service2 on the same day & Prefer working service1+, service2+ on the same day
        for date in self.work_dates:
            objectives[f'Prefer working service1, service2 on the same day on {date}'] = []
            objectives[f'Prefer working service1+, service2+ on the same day on {date}'] = []
            for employee in self.employees:
                ser1 = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date.date() and shift.type in ['service1']]
                ser2 = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date.date() and shift.type in ['service2']]
                ser1p = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date.date() and shift.type in ['service1+']]
                ser2p = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date.date() and shift.type in ['service2+']]
                objectives[f'Prefer working service1, service2 on the same day on {date}'].append(sum(ser1) == sum(ser2))
                objectives[f'Prefer working service1+, service2+ on the same day on {date}'].append(sum(ser1p) == sum(ser2p))


        # objectives[f'Prefer working service1, service2 on the same day'] = []
        # objectives[f'Prefer working service1+, service2+ on the same day'] = []
        # # penalty = 1
        # # self.__penalties = self.__model.NewIntVar(0, 100000, 'penalties')
        # for date in self.work_dates:
        #     for employee in self.employees:
        #         # Give penalties if working service1, service2 on the different day
        #         ser1 = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date and shift.type in ['service1']]
        #         ser2 = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date and shift.type in ['service2']]
        #         ser1p = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date and shift.type in ['service1+']]
        #         ser2p = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.date == date and shift.type in ['service2+']]
        #         # objectives[f'Prefer working service1, service2 on the same day on {date}'].append(sum(ser1) == sum(ser2))
        #         # objectives[f'Prefer working service1+, service2+ on the same day on {date}'].append(sum(ser1p) == sum(ser2p))
        #         objectives[f'Prefer working service1, service2 on the same day'].append(sum(ser1) + sum(ser2) != 1)
        #         objectives[f'Prefer working service1+, service2+ on the same day'].append(sum(ser1p) + sum(ser2p) != 1)




        # [3] Distribution of workload, Minimize the number of shifts assigned to employees on the same day, 1 shift per employee per day if possible, except for service1 and service2
        # for date in self.dates:
        #     objectives[f'Minimize the number of shifts assigned to each employee on {date.date()}'] = []
        #     for employee in self.employees:
        #         objectives[f'Minimize the number of shifts assigned to each employee on {date.date()}'].append(sum([self.__shift_vars[(shift, employee)] for shift in self.get_shifts_by_date(date)]) <= 1)
                

        # [2] Avoid working on the consecutive days
        # shift_group_for_distribution = [
        #     ('service1', 'service2', 'service1+', 'service2+'),
        #     ('mc'),
        #     ('amd', 'avd'),
        #     ('avd')
        # ]
        # duration = 1 #days
        # for employee in self.employees:
        #     for shift_type in shift_group_for_distribution:
        #         shifts = [shift for shift in self.shifts if shift.type in shift_type] # Shifts = [shift1, shift2, ...] for each shift type
        #         for shift1 in shifts:
        #             for shift2 in [shift for shift in shifts if shift != shift1 and shift.start > shift1.start and shift.start - shift1.start <= timedelta(days=duration)]:
        #                 objectives[f'Avoid working {shift_type} on the consecutive days for {employee.abbreviation} between {shift1.title} & {shift2.title}'] = []
        #                 objectives[f'Avoid working {shift_type} on the consecutive days for {employee.abbreviation} between {shift1.title} & {shift2.title}'].append(self.__shift_vars[(shift1, employee)] + self.__shift_vars[(shift2, employee)] <= 1)

        # [3.1] Prefer working service1, service2 on the same day    
        # [3.2] Prefer working service1+, service2+ on the same day
                



        # for date in self.work_days:
        #     objectives[f'Prefer working service1, service2 on the same day on {date}'] = []
        #     objectives[f'Prefer working service1+, service2+ on the same day on {date}'] = []
        #     for employee in self.employees:
        #         ser1 = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.start.date() == date and shift.type in ['service1']]
        #         ser2 = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.start.date() == date and shift.type in ['service2']]
        #         ser1p = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.start.date() == date and shift.type in ['service1+']]
        #         ser2p = [self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.start.date() == date and shift.type in ['service2+']]
        #         objectives[f'Prefer working service1, service2 on the same day on {date}'].append(sum(ser1) == sum(ser2))
        #         objectives[f'Prefer working service1+, service2+ on the same day on {date}'].append(sum(ser1p) == sum(ser2p))
  
        # [4] Shift Preference, some employees prefer to work in the morning, some prefer to work in the afternoon
        # shift_preference = {
        #     'BC' : 'morning',
        #     'KL' : None,
        #     'UT' : 'afternoon'
        #     ...
        # }


        # for employee in self.employees:
        #     if self.__shift_preference[employee.abbreviation] is None:
        #         continue
        #     morning_shifts = sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['service1']])
        #     afternoon_shifts = sum([self.__shift_vars[(shift, employee)] for shift in self.shifts if shift.type in ['service2']])

        #     shift_diff = morning_shifts - afternoon_shifts if self.__shift_preference[employee.abbreviation] == 'morning' else afternoon_shifts - morning_shifts
        #     objective_key = f'Shift preference for {employee.abbreviation} soft'

        #     # Add the soft constraint directly to the objective
        #     max = math.floor(self.shift_per_employee('service1') + self.shift_per_employee('service2')) + 1
        #     for i in range(1, 5):
        #         objectives[objective_key + f', preference delta = {i}'] = []

        #     for i in range(1, 5):    
        #         objectives[objective_key + f', preference delta = {i}'].append(shift_diff >= i)

         

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

        self.logger.info('Begin solving for the schedule, with following rules:')
        self.logger.info('Rule 1: Each shift must be assigned to employees more than or equal to min_employees, and less than or equal to max_employees')
        self.logger.info('Rule 2: If the shift is assigned to employees, fixed the shift assigned to the employees')
        self.logger.info('Rule 3: The shift should only be assigned to the employees who are available (Compare to employee\'s tasks), except for fixed shifts')
        self.logger.info('Rule 4: Some shifts cannot be assigned to the same employee in the same day, represent with a logical matrix, exclude fixed shifts')
        self.logger.info(f'Rule 5: Fair distribution of shifts per employee per shift type')
        for group in shift_group_sum:
            self.logger.info(f'    {group[0]} shifts per employee per {group[1]} = {shift_group_sum[group]}')
        self.logger.info(f'Rule 6: Manual set number of shifts per employee')
        for e, shift_sum in shift_sum_employee.items():
            self.logger.info(f'    {e} - {shift_sum}')
        self.logger.info('')
        self.logger.info('Result:')

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 300
        solver.parameters.num_search_workers = 8
        
        # solve model with incremental constraints, if no solution, reset the model and add the constraints again, skip the date
        constraint_complete = True
        model_before_become_infeasible = cp_model.CpModel()
        solver_before_become_infeasible = cp_model.CpSolver()

        try: 
            for date in self.days:
                model_before_become_infeasible.CopyFrom(self.__model)
                for constraint in date_constraints[date]:
                    self.__model.Add(constraint)
                status = solver.Solve(self.__model)
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    continue
                else:
                    self.logger.info(f'❌ No solution found for {date}')
                    print(f'No solution found for {date}')
                    self.__model.CopyFrom(model_before_become_infeasible)
                    constraint_complete = False
                    continue 

            for employee in self.employees:
                model_before_become_infeasible.CopyFrom(self.__model)
                for constraint in employee_constraints[employee]:
                    self.__model.Add(constraint)
                    # self.logger.debug(f'Added constraint for {employee.abbreviation} - {constraint}')
                status = solver.Solve(self.__model)
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    continue
                else:
                    self.logger.info(f'❌ No solution found for {employee.abbreviation}')
                    self.__model.CopyFrom(model_before_become_infeasible)
                    constraint_complete = False
                    continue

            objective_choice = 1
            # Add objectives, if no solution, reset the model and add the new objectives, skip the objective
            if constraint_complete:
                self.logger.info('✅︎ All rules are satisfied, now optimizing the schedule with following objectives:')
                
                for objective_name, objective_group in objectives.items():
                    model_before_become_infeasible.CopyFrom(self.__model)
                    for objective in objective_group:
                        # pass
                        self.__model.Add(objective)
                    status = solver.Solve(self.__model)
                    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                        self.logger.info('✅︎ Objective: {}'.format(objective_name))
                        # status = solver_before_become_infeasible.Solve(self.__model)
                        continue
                    else:
                        print(f'No solution found for {objective_name}')
                        self.logger.info('❌ Objective: {}'.format(objective_name))
                        self.__model.CopyFrom(model_before_become_infeasible)
                        continue
            
                status = solver.Solve(self.__model)
                
            else:
                self.logger.info("❌ The schedule is not optimized, because the rules are not satisfied")

            
        except Exception as e:
            self.logger.info("❌ The program exited with an error")
            self.logger.info("Error: {}".format(e))

        # Update the shifts and employees
        for shift in self.shifts:
            for employee in self.employees:
                try:
                    if solver.Value(self.__shift_vars[(shift, employee)]) == 1:
                    # print(f'{shift.name} is assigned to {employee.name}')
                        shift.add_employee(employee)
                        employee.add_shift(shift)
                        self.logger.debug(f'{shift.title} is assigned to {employee.abbreviation}')
                except Exception as e:
                    # self.logger.debug(f'{shift.title} is not assigned to {employee.abbreviation} due to {e}')
                    continue
                
        self.schedule.shifts = self.shifts
        self.schedule.employees = self.employees
        self.logger.info("Schedule Updated!")
        return self.schedule          

    
    def get_solution(self):
        pass
    
    def get_status(self):
        pass