from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from source import *



class GoogleSheetApp():
    def __init__(self, creds = None):
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = None

        try:
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
        except Exception as e:
            print(f'Error: {e}')

        self.creds = creds
        service = build('sheets', 'v4', credentials=self.creds)
        self.service = service
        self.sheet = service.spreadsheets()

    def get_sheet_values(self, spreadsheet_id, range_name, type = 'values'):
        result = self.sheet.values().get(spreadsheetId=spreadsheet_id,
                                        range=range_name).execute()
        values = result.get('values', [])
        if type == 'values':
            return values
        elif type == 'dict':
            titles = values[0]
            values = values[1:]
            result = [dict(zip(titles, value)) for value in values]
            return result
        
    def update_sheet_values(self, spreadsheet_id, range_name, values):
        body = {
            'values': values
        }
        result = self.sheet.values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='USER_ENTERED', body=body).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))


class SchedulerApp:
    def __init__(self):
        self.googleSheetApp = GoogleSheetApp()
        self.__sheet_id = '1wHNERHZUxl8mI7xOPtWsvRBHxw9r_ohFoi7BWET_YdU'
        self.__morning_availability_range = 'Working table!AS3:BC34'
        self.__afternoon_availability_range = 'Working table!BE3:BO34'
        self.__fixed_shift_range = 'Working table!AI3:AQ34'
        self.__staffs_range = 'staffs!A1:G13'
        self.__name_range = 'Working table!A3'
        self.__shifts_range = 'Working table!Y3:AG34'
        self.__output_range = 'Working table!AI4:AQ34'
        self.__holidays_range = 'Working table!X4:X34'

        name = self.get_schedule_name()
        schedule = Schedule(
            name = name,
            start_time= datetime(2023, 4, 1),
            end_time= datetime(2023, 4, 30),
        )

        # Add active employees to schedule
        employees = self.get_staffs()
        for employee in employees: #type: ignore
            if employee['active'] == 'TRUE':
                schedule.add_employee(
                    Employee(
                        first_name=employee['first_name'],
                        last_name=employee['last_name'],
                        role=employee['role'],
                        abbreviation=employee['abbreviation'],
                    )
                )
        
        # Add shifts to schedule
        shifts = self.get_shifts() #type: ignore
        shifts_header = [str.lower(i) for i in shifts[0]] #type: ignore
        shifts = shifts[1:] #type: ignore
        for j in range(len(shifts)): #type: ignore
            for i in range(len(shifts_header)):
                if shifts[j][i] == 'TRUE':
                    if shifts_header[i] in ['mc', 's1', 's1+']:
                        start_time = datetime(2023, 4, 1, 8, 0, 0) + timedelta(days=j)
                        hours = 4
                    elif shifts_header[i] in ['s2', 's2+']:
                        start_time = datetime(2023, 4, 1, 12, 0, 0) + timedelta(days=j)
                        hours = 4
                    else:
                        start_time = datetime(2023, 4, 1, 8, 0, 0) + timedelta(days=j)
                        hours = 8

                    schedule.add_shift(
                        Shift(
                            name = shifts_header[i],
                            description = shifts_header[i],
                            start_time = start_time,
                            duration = timedelta(hours=hours),
                            shift_type = shifts_header[i],
                        )
                    )

        # Add fixed shifts
        fixed_shifts = self.get_fixed_shift() #type: ignore
        # print('Fixed shifts:')
        fixed_shifts_header = [str.lower(i) for i in fixed_shifts[0]] #type: ignore
        fixed_shifts = fixed_shifts[1:] #type: ignore
        for row_index in range(len(fixed_shifts)): #type: ignore
            row = fixed_shifts[row_index]
            for col_index in range(len(row)):
                if row[col_index] != '':
                    date = datetime(2023, 4, 1+row_index)
                    shifts = schedule.get_shifts_by_date(date)
                    # print(f'{date} => {shifts}')
                    for shift in [s for s in shifts if s.shift_type == fixed_shifts_header[col_index]]:
                        for employee in schedule.employees:
                            if employee.abbreviation == row[col_index]:
                                # print(f'    {employee.abbreviation} => {shift}')
                                schedule.assign_shift(shift, employee)
                    

        # Add morning availability
        morning_availability = self.get_morning_availability()
        for i in range(len(morning_availability)): #type: ignore
            for employee in schedule.employees:
                abbreviation = employee.abbreviation
                if morning_availability[i][abbreviation] == 'FALSE': #type: ignore
                    employee.add_task(
                        Task(name="", description="", start_time = datetime(2023, 4, i+1, 8, 0, 0), duration = timedelta(hours=4))
                    )
        
        # Add afternoon availability
        afternoon_availability = self.get_afternoon_availability()
        for i in range(len(afternoon_availability)): #type: ignore
            for employee in schedule.employees:
                abbreviation = employee.abbreviation
                if afternoon_availability[i][abbreviation] == 'FALSE': #type: ignore
                    employee.add_task(
                        Task(name="", description="", start_time = datetime(2023, 4, i+1, 12, 0, 0), duration = timedelta(hours=4))
                    )

        #Add holidays
        holidays = self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__holidays_range, type = 'values')
        for index in range(len(holidays)): #type: ignore
            if holidays[index][0] == 'TRUE': #type: ignore
                schedule.add_holiday(datetime(2023, 4, 1 + index))
                # print(f'Add holiday: {datetime(2023, 4, 1 + index)}')
            

        self.__schedule = schedule

    @property
    def schedule(self):
        return self.__schedule

    def get_schedule_name(self):
        return self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__name_range, type = 'values')[0][0] #type: ignore

    def get_morning_availability(self):
        result =  self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__morning_availability_range, type = 'dict')
        return result
    
    def get_afternoon_availability(self):
        return self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__afternoon_availability_range, type = 'dict')
    
    def get_fixed_shift(self):
        return self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__fixed_shift_range, type = 'values')
    
    def get_staffs(self):
        return self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__staffs_range, type = 'dict')
    
    # def get_staffs_abbreviation(self):
    #     abbreviation = {}
    #     result = self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__staffs_range, type = 'dict')
    #     for staff in result: #type: ignore
    #         abbreviation[staff['first_name']] = staff['abbreviation']
    #     return 
    
    def get_shifts(self):
        return self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__shifts_range, type = 'values')
    
    def update_schedule(self)-> None:
        self.googleSheetApp.update_sheet_values(self.__sheet_id, self.__output_range, self.schedule.to_matrix())
        pass

    def get_holidays(self):
        return self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__holidays_range, type = 'values')

    def solve(self):
        self.schedule.solve()
        
    

if __name__ == '__main__':
    schedulerApp = SchedulerApp()
    
    schedulerApp.solve()
    schedulerApp.schedule.show(format='table')
    schedulerApp.update_schedule()
    # schedulerApp.schedule.show(format='table', group_by='workload')

    # print(schedulerApp.schedule.to_matrix())

    

    # result = schedulerApp.get_morning_availability()
    # print(result)
    
 
    # morning_task = Task(name='morning_task', description="", start_time=datetime(2023, 3, date, 8, 0), duration=timedelta(hours=4))
    # afternoon_task = Task(name='afternoon_task', description="", start_time=datetime(2023, 3, date, 12, 0), duration=timedelta(hours=4))
    # all_day_task = Task(name='all_day_task', description="", start_time=datetime(2023, 3, date, 8, 0), duration=timedelta(hours=8))
    

    # for i in range(len(result)): #type: ignore
    #     for employee in schedulerApp.schedule.employees:
    #         abbreviation = employee.abbreviation
    #         if result[i][abbreviation] == 'TRUE': #type: ignore
    #             print(f'{employee.first_name} is available on {i+1}th')

