from datetime import datetime, timedelta
from .schedule import *

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
    def __init__(self, schedule: Schedule):
        self.schedule = schedule
        self.model = None # Initialize model - gurobi, ortools, etc
        self.constraints = []
        self.constraint_groups = []
        self.status = '' # unsolved, infeasible, feasiblem optimal
        self.solutions = []
    
    def add_constraint(self, constraint: SchedulerConstraint):
        self.constraints.append(constraint)
        # then  solve constraints group by group

    def visualize(self):
        '''Visualize schedule using matplotlib, plotly, etc.'''
        pass
        # visualize schedule

    def check_feasibility(self):
        pass
        # solve only constraint group by group
    
    def solve(self):
        pass
    
    def get_solution(self):
        pass
    
    def get_status(self):
        pass
    