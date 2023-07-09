from source import *

from googlesheetapp import GoogleSheetApp



class SchedulerApp:
    def __init__(self):
        self.googleSheetApp = GoogleSheetApp()
        self.__sheet_id = '1wHNERHZUxl8mI7xOPtWsvRBHxw9r_ohFoi7BWET_YdU'
        self.__morning_availability_range = 'Interface demo!B72:M103'
        self.__afternoon_availability_range = 'Interface demo!B107:M138'
        self.__fixed_shift_range = 'Interface demo!C145:K176' # include header
        self.__staffs_range = 'Interface demo!A47:G67'
        self.__name_range = 'Interface demo!E5'
        self.__shifts_range = 'Interface demo!C11:K42'
        self.__output_range = 'Interface demo!C233:K263'
        self.__holidays_range = 'Interface demo!B12:B42' #exclude header
        self.__date_range = 'Interface demo!A12:A42'
        self.__shift_matrix_range = 'Interface demo!A210:J219' #TODO: retrieve shift matrix from sheet

        start_date, end_date = self.get_date()

        self._start_date = start_date
        self._end_date = end_date

        name = self.get_schedule_name()
        schedule = Schedule(
            name = name,
            start_time= self._start_date,
            end_time= self._end_date,
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
        
        # TODO : setting shift types from sheet
        # Add shifts to schedule
        shifts = self.get_shifts() #type: ignore
        shifts_header = [str.lower(i) for i in shifts[0]] #type: ignore
        shifts = shifts[1:] #type: ignore
        for j in range(len(shifts)): #type: ignore
            for i in range(len(shifts_header)):
                if shifts[j][i] == 'TRUE':
                    if shifts_header[i] in ['mc', 's1', 's1+']:
                        start_time = self._start_date + timedelta(days=j, hours=8)
                        duration = 4 #hours
                    elif shifts_header[i] in ['s2', 's2+']:
                        start_time = self._start_date + timedelta(days=j, hours=12)
                        duration = 4
                    else:
                        start_time = self._start_date + timedelta(days=j, hours=8)
                        duration = 8

                    schedule.add_shift(
                        Shift(
                            name = shifts_header[i],
                            description = shifts_header[i],
                            start_time = start_time,
                            duration = timedelta(hours=duration),
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
                    date = self._start_date + timedelta(days=row_index)
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
                    
                    start_time = self._start_date + timedelta(days=i, hours=8)

                    employee.add_task(
                        Task(name="", description="", start_time = start_time, duration = timedelta(hours=4))
                    )
        
        # Add afternoon availability
        afternoon_availability = self.get_afternoon_availability()
        for i in range(len(afternoon_availability)): #type: ignore
            for employee in schedule.employees:
                abbreviation = employee.abbreviation
                if afternoon_availability[i][abbreviation] == 'FALSE': #type: ignore
                    start_time = self._start_date + timedelta(days=i, hours=12)
                    employee.add_task(
                        Task(name="", description="", start_time = start_time, duration = timedelta(hours=4))
                    )

        #Add holidays
        holidays = self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__holidays_range, type = 'values')
        for index in range(len(holidays)): #type: ignore
            if holidays[index][0] == 'TRUE': #type: ignore
                holiday = self._start_date + timedelta(days=index)
                schedule.add_holiday(holiday)
                # print(f'Add holiday: {datetime(2023, 4, 1 + index)}')
            
        self.__schedule = schedule

    @property
    def schedule(self):
        return self.__schedule
    
    @property
    def staffs(self):
        return self.__schedule.employees
    
    @property
    def shifts(self):
        return self.__schedule.shifts

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
        print('Update schedule successfully')
        pass

    def get_holidays(self):
        return self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__holidays_range, type = 'values')

    def get_date(self):
        date_text = self.googleSheetApp.get_sheet_values(self.__sheet_id, self.__date_range, type = 'values') #type: ignore
        start_date = datetime.strptime(date_text[0][0], '%d/%m/%Y') #type: ignore
        end_date = datetime.strptime(date_text[-1][0], '%d/%m/%Y') #type: ignore

        return start_date, end_date

    def solve(self):
        self.schedule.solve()
        
    

if __name__ == '__main__':
    schedulerApp = SchedulerApp()

    # print(schedulerApp.staffs)
    # print(schedulerApp.shifts)

    # print(schedulerApp.get_date())

    
    schedulerApp.solve()
    schedulerApp.schedule.show(format='table')
    schedulerApp.update_schedule()
    schedulerApp.schedule.show(format='table', group_by='workload')

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

