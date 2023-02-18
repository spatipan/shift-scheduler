# Description: This file contains the classes for the objects.

# Staff class contains the information about the staff members.
class Staff():
    def __init__(self, name, is_ai):
        self.name = name
        self.is_ai = is_ai

# Shift class contains the information about the shifts.
class Shift():
    def __init__(self, name):
        self.name = name

# ShiftRequest class contains the information about the shift requests.
class ShiftRequest():
    def __init__(self, staff, shift, day, priority):
        self.staff = staff
        self.shift = shift
        self.day = day
        self.priority = priority  # 1 is highest priority, 3 is lowest priority

