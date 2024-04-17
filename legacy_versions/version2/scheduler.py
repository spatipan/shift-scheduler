from ortools.sat.python import cp_model
from time import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import ortools

#import local module
from src.utils.utils import get_holiday, get_morn_con_day


# ============================= Input ============================= #

# List of staffs
staff_names = ["อ.บริบูรณ์","อ.ณัฐฐิกานต์","อ.ปริญญา","อ.ภาวิตา","อ.ธีรพล","อ.บวร","อ.ชานนท์","อ.บุญฤทธิ์","อ.กอสิน","อ.พิมพ์พรรณ","อ.กรองกาญจน์"]
num_staffs = len(staff_names)

# Select month and year to schedule & 
month = 3
year = 2023
num_days = (datetime(year, month+1, 1) - datetime(year, month, 1)).days
date_list = [datetime(year, month, day) for day in range(1, num_days+1)]

#Get holiday list
holiday = get_holiday(year, month)

#Get morn con day list
morn_con_day = get_morn_con_day(year, month)

# List of shifts
shift_names = ['off', 'service1', 'service2', 'service1+', 'service2+', 'Observe', 'Morn Con', 'EMS',  'AMD']
num_shifts = len(shift_names) # 9 shifts per day


def schedule_shifts():
    # ============================= Create model ============================= #

    model = cp_model.CpModel()

    # Create shift variables.
    # shifts[(s, d, w)]: staff 's' works shift 'w' on day 'd'.
    shifts = {}
    for s in range(num_staffs):
        for d in range(num_days):
            for w in range(num_shifts):
                shifts[(s, d, w)] = model.NewBoolVar('shift_s%id%iw%i' % (s, d, w))

    # ============================= Required Constraints ============================= #

    # For (EMS & AMD) Each shift is assigned to exactly one staff in that day, include holiday
    for d in range(num_days):
        for w in [7, 8]:
            model.AddExactlyOne([shifts[(s, d, w)] for s in range(num_staffs)])

    # For (service1 & service2 & service1+ & service2+ & observe) Each shift is assigned to exactly one staff in that day, exclude holiday
    for d in range(num_days):
        if holiday[d] == False:
            for w in [1, 2, 3, 4, 5]:
                model.AddExactlyOne([shifts[(s, d, w)] for s in range(num_staffs)])

    # For morning conference day, each staff must work at least 1 shift
    for d in range(num_days):
        if morn_con_day[d] == True:
            model.AddExactlyOne([shifts[(s, d, 6)] for s in range(num_staffs)])

    # Each staff works at most one shift per day.
    for s in range(num_staffs):
        for d in range(num_days):
            model.AddExactlyOne([shifts[(s, d, w)] for w in range(num_shifts)])

    # ============================= Optional Constraints ============================= #







    # ============================= Solve ============================= #


    # Solution printer.
    class ShiftSolutionPrinter(cp_model.CpSolverSolutionCallback):

        def __init__(self, shifts, num_staffs, num_days, num_shifts):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._shifts = shifts
            self._num_staffs = num_staffs
            self._num_days = num_days
            self._num_shifts = num_shifts
            self._solution_count = 0
            self._solutions = []
            self._workloads = []

        def OnSolutionCallback(self):
            self._solution_count += 1

            #Workload per staff
            workload = np.zeros(self._num_staffs)
            for s in range(self._num_staffs):
                for d in range(self._num_days):
                    for w in range(1, self._num_shifts): # exclude 'off'
                        workload[s] += self.Value(self._shifts[(s, d, w)])
            # print(workload)
            self._workloads = workload


            ls=[]
            for d in range(self._num_days):
                ls_day=[]
                for w in range(self._num_shifts):
                    ls_shift=[]
                    for s in range(self._num_staffs):
                        if self.Value(self._shifts[(s, d, w)]):
                            ls_shift.append(staff_names[s])
                    ls_day.append(ls_shift)
                ls.append(ls_day)
            
            df = pd.DataFrame(ls, index=date_list, columns=shift_names)
            print(df)
            self._solutions.append(df)

            # df.to_csv('schedule.csv', index=True, header=True)

        def get_solutions(self):
            return self._solutions

        def get_solution(self):
            return self._solutions.pop()

        def workloads(self):
            return self._workloads

        


    # Solve model.
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    solution_printer = ShiftSolutionPrinter(shifts, num_staffs, num_days, num_shifts)
    status = solver.Solve(model, solution_printer)
    # status = solver.Solve(model)
    print(solver.ResponseStats())

    return solution_printer