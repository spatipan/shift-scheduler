from modules.google_app.sheet import GoogleSheetApp
from modules.scheduler_app.models.models import Employee, Shift, Task, Event, Schedule
from modules.scheduler_app.solver import ScheduleSolver
import logging
import config
import re
from datetime import datetime, timedelta
import calendar
import numpy as np 

import pandas as pd

class SchedulerSheetUI:
    '''Sheet UI for the scheduler app.
    use Google Sheet as UI for the scheduler app
    and store the data in the Google Sheet
    '''
    def __init__(self, sheetApp: GoogleSheetApp, 
                 sheetId: str,
                 sheetName: str):
        self.sheetApp = sheetApp
        self.sheetName = sheetName
        self.sheetId = sheetId
        self.sheet_vaules = None
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.debug(f'SchedulerSheetUI initialized - sheetId: {sheetId}')

        self.schedule = Schedule()
        self.solver = ScheduleSolver()

        self.fetch_sheet_values()

    # Fetch all sheet values from the given
    def fetch_sheet_values(self, range: str = 'A1:V') -> list[list]:
        '''Fetches all values from google sheet'''

        self.sheet_values = self.sheetApp.read(spreadsheetId=self.sheetId, sheetName=self.sheetName, range=range)

        # convert to pandas dataframe, to fill the empty cells with None
        df = pd.DataFrame(self.sheet_values)
        self.sheet_values = df.values.tolist()

        self.logger.debug(f'Fetched sheet values from {range}')
        return self.sheet_values
    
    # Extract information from the fetched values (Date, Employees, Shifts, Fixed Shifts, Tasks, Holidays, Constraints)
    def extract_sheet_values(self):
        '''Extracts information from the fetched values
        (Employees, Shifts, Fixed Shifts, Holidays, Constraints)'''

        # Get start and end date
        start_date = datetime.strptime(self.get_sheet_values(range=config.DATE_RANGE)[0][0], '%d/%m/%Y')
        days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = start_date + timedelta(days = days_in_month - 1, hours=23, minutes=59, seconds=59, microseconds= 99999)

        self.schedule.start = start_date
        self.schedule.title = f'Schedule of {start_date.strftime("%B %Y")}'
        self.schedule.end = end_date

        # Get employees
        employees = self.get_sheet_values_as_dict(range=config.EMPLOYEE_RANGE)
        employees = [Employee.from_dict(e) for e in employees if e['active'] == 'TRUE'] # Get active employees only
        self.schedule.employees = employees

        # Get shifts
        shift_values = self.get_sheet_values(config.SHIFT_RANGE)
        shifts_header = [str.lower(i) for i in shift_values[0]] #type: ignore
        shift_data = shift_values[1:] #type: ignore
        shifts = []
        for j in range(len(shift_data)): #type: ignore
            for i in range(len(shifts_header)):
                if shift_data[j][i] == 'TRUE':
                    if shifts_header[i] in ['mc', 'service1', 'service1+']:
                        start_time = start_date + timedelta(days=j, hours=8)
                        duration = 4 #hours
                    elif shifts_header[i] in ['service2', 'service2+']:
                        start_time = start_date + timedelta(days=j, hours=12)
                        duration = 4
                    elif shifts_header[i] in ['service night']:
                        start_time = start_date + timedelta(days=j, hours=0)
                        duration = 8
                        # print(f'Add night shift on {start_time} - {start_time + timedelta(hours=8)}')
                    else:
                        start_time = start_date + timedelta(days=j, hours=8)
                        duration = 8
                    new_shift = Shift(
                        title= f'{shifts_header[i].capitalize()} - {start_time.strftime("%Y-%m-%d")}',
                        type=shifts_header[i],
                        start=start_time,
                        end=start_time + timedelta(hours=duration)
                    )
                    shifts.append(new_shift)
        for shift in shifts:
            shift.start = shift.start.astimezone(tz= config.TIMEZONE)
            shift.end = shift.end.astimezone(tz= config.TIMEZONE)
        self.schedule.shifts = shifts

        # Get fixed shifts
        fixed_shifts_values = self.get_sheet_values(range=config.FIXED_SHIFT_RANGE)
        # print(fixed_shifts_values)

        fixed_shifts_header = [str.lower(i) for i in fixed_shifts_values[0]] 
        fixed_shift_data = np.array(fixed_shifts_values[1:])
        fixed_shift_data = np.where(fixed_shift_data == None, '', fixed_shift_data)

        for row in range(len(fixed_shift_data)):
            for col in range(len(fixed_shift_data[row])):
                if fixed_shift_data[row][col] != '':
                    # filter the shifts by row(date) and column(shift type)
                    date = start_date + timedelta(days=row)
                    shifts = self.schedule.get_shifts_by_date(date)
                    for shift in [s for s in shifts if s.type == fixed_shifts_header[col]]:
                        for employee in [e for e in  self.schedule.employees if e.abbreviation == fixed_shift_data[row][col]]:
                            self.schedule.assign_shift(shift, employee)
                    
        
        #Add holidays
        holidays_values = self.get_sheet_values(range=config.HOLIDAYS_RANGE)
        for index in range(len(holidays_values)): #type: ignore
            if holidays_values[index][0] == 'TRUE': #type: ignore
                holiday = self.schedule.start + timedelta(days=index)
                self.schedule.add_holiday(holiday)

                  

        ################# Constraints #################
                
        #Add Total service constraint
        total_shift_constraint = self.get_sheet_values(range = config.TOTAL_SHIFT_CONSTRAINT)
        for row in total_shift_constraint: #type: ignore
            if len(row) == 2 and row[0] != '' and row[1] != '':
                staff_abbreviation = row[0]
                total_shift = int(row[1])
                self.solver.add_total_shifts_constraint(staff_abbreviation, total_shift)
            else:
                continue

        #Add shift preference (week day)
        shift_preference = self.get_sheet_values(range = config.SHIFT_PREFERENCE_RANGE)
        for row in shift_preference:
            if len(row) == 6 and row[0] != '':
                staff_abbreviation = row[0]
                monday = True if row[1] == 'TRUE' else False
                tuesday = True if row[1] == 'TRUE' else False
                wednesday = True if row[1] == 'TRUE' else False
                thursday = True if row[1] == 'TRUE' else False
                friday = True if row[1] == 'TRUE' else False
                self.solver.add_shift_preference_constraint(staff_abbreviation, monday, tuesday, wednesday, thursday, friday)
        

        #Add shift type per employee constraint
        shift_type_per_employee = self.get_sheet_values(range = config.SHIFT_TYPE_PER_EMPLOYEE_RANGE)
        # delete column 1
        shift_type_per_employee = np.delete(shift_type_per_employee, 1, 1)
        header = shift_type_per_employee[0]
        # shift_types = [str.lower(shift_type) for shift_type in header[1:] if str.lower(shift_type) in ['service night', 'mc', 'service1', 'service1+', 'service2', 'service2+', 'ems', 'observe', 'amd', 'avd']]
        body = shift_type_per_employee[1:]
        for row in body: #type: ignore
            if row[0] != '':
                employee_abbreviation = row[0]
                for i in range(1, len(row)):
                    if row[i] != '':
                        shift_type = str.lower(header[i])
                        self.solver.add_shift_type_per_employee_constraint(employee_abbreviation, shift_type, int(row[i]))
                    else:
                        continue

            


        return self.schedule, self.solver


        
    def get_sheet_values(self, range: str) -> list[list]:
        '''Get sheet values from fetched values'''
        start, end = self.a1_range_to_index_range(range)
        df = pd.DataFrame(self.sheet_values)
        values = df.iloc[start[0]:end[0]+1, start[1]:end[1]+1].values.tolist()
        self.logger.debug(f'Got sheet values from {range}, start: ({start[0]}, {start[1]}), end: ({end[0]}, {end[1]})')
        return values
    
    def get_sheet_values_as_dict(self, range: str) -> list[dict]:
        '''Get sheet values from fetched values'''
        values = self.get_sheet_values(range)
        header = values[0]
        values = values[1:]
        result = [dict(zip(header, value)) for value in values]
        return result

    # Update sheet with the schedule
    def update_sheet_values(self, schedule: Schedule):
        '''Update the sheet values with the schedule'''
        # Update the sheet with the schedule
        self.sheetApp.update(spreadsheetId=self.sheetId, sheetName=self.sheetName, range=config.OUTPUT_RANGE, values=schedule.to_sheet_values())
        self.logger.debug(f'Updated sheet values with the schedule \n  - Schedule: {schedule} \n  - Range: {config.OUTPUT_RANGE} \n  - Sheet: {self.sheetName} \n  - SheetId: {self.sheetId}')


    # static method to translate A1 notation to index
    @staticmethod
    def a1_to_index(cell: str) -> tuple[int, int]:
        """
        Converts a cell address in A1 notation to a dictionary containing row and column index (0-based).

        Args:
            cell: The cell address as a string in A1 notation (e.g., "A1", "AA25", "ZZ999").

        Returns:
            A dictionary with keys 'row' and 'column' containing the 0-based row and column indices.
            Returns None if the input is not valid A1 notation.
        """
        cell = cell.upper()
        match = re.search(r"([A-Z]+)([0-9]+)", cell)
        if not match:
            raise ValueError(f'Invalid cell address: {cell}')

        column_letters, row_string = match.groups()

        # Convert column letters to a number (0-based)
        column = 0
        for i, char in enumerate(reversed(column_letters)):
            # Consider the position of the character (number of letters before)
            column += (26 ** i) * (ord(char) - ord('A') + 1)
        
        column -= 1

        # Convert row string to a number (0-based)
        row = int(row_string) - 1

        logging.debug(f'Converted {cell} to {row}, {column}')

        return row, column
    
    # static method to translate A1 range to index range
    @staticmethod
    def a1_range_to_index_range(range: str) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Converts a range in A1 notation to a dictionary containing row and column indices (0-based).

        Args:
            range: The range as a string in A1 notation (e.g., "A1:B2", "AA25:ZZ999").

        Returns:
            A dictionary with keys 'start' and 'end' containing the 0-based row and column indices.
            Returns None if the input is not valid A1 notation.
        """
        start, end = range.split(':')
        start = SchedulerSheetUI.a1_to_index(start)
        end = SchedulerSheetUI.a1_to_index(end)
        return start, end
    

if __name__ == '__main__':
    
    #Test A1 to index
    assert SchedulerSheetUI.a1_to_index('A1') == (0, 0)