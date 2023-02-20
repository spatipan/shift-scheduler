from datetime import datetime
from timeinterval import TimeInterval, TimeIntervals
from shift import Shift

# Create employee class, which contains the employee's name, 
# and the time intervals that the employee is available for given periods of time
# assigned shifts will be stored in a list, which will be updated as the schedule is created
# and the employee's availability will be updated as shifts are assigned
class Employee:
    def __init__(self, name: str, age :int, gender: str,  availability: TimeIntervals):
        self.name = name
        assert age > 0, "Age must be greater than 0"
        self.age = age
        assert (gender != "male") or (gender != "female"), "gender must be 'male' or 'female'"
        self.gender = gender
        self.availability = availability
        self.assigned_shifts = []
    
    # add a shift to the employee's assigned shifts
    def add_shift(self, shift):
        self.assigned_shifts.append(shift)
    
    # remove a shift from the employee's assigned shifts
    def remove_shift(self, shift):
        self.assigned_shifts.remove(shift)
        
    # # visualize the employee's availability
    # def visualize_availability(self):
    #     self.availability.visualize_gantt()
        
    # # visualize the employee's assigned shifts
    # def visualize_assigned_shifts(self):
    #     fig = ff.create_gantt(self.assigned_shifts)
    #     fig.show()
    
