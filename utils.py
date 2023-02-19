from datetime import datetime, timedelta


# Check special holiday
# TODO: add more special holiday yearly DUE DATE: 2023-12-31
thai_special_holiday = [
datetime(2023, 1, 2), # วันหยุดชดเชยปีใหม่
datetime(2023, 3, 6), # วันมาฆบูชา
datetime(2023, 4, 6), # วันจักรี
datetime(2023, 4, 13), # วันสงกรานต์
datetime(2023, 4, 14), # วันสงกรานต์
datetime(2023, 4, 17), # วันหยุดชดเชยสงกรานต์
datetime(2023, 5, 4), # วันฉัตรมงคล
datetime(2023, 5, 5), # วันฉัตรมงคล หยุดพิเศษ
datetime(2023, 5, 17), # วันพืชมงคล
datetime(2023, 6, 5), # วันหยุดชดเชย
datetime(2023, 7, 28), # วันเกิด ร.10
datetime(2023, 8, 1), # วันอาสาฬหบูชา
datetime(2023, 8, 2), # วันเข้าพรรษา
datetime(2023, 8, 14), # วันหยุดชดเชยวันแม่
datetime(2023, 10, 13), # วันสวรรคต ร.9
datetime(2023, 10, 23), # วันปิยมหาราช
datetime(2023, 12, 5), # วันพ่อ
datetime(2023, 12, 11), # วันหยุดชดเชยวันรัฐธรรมนูญ
]

# define function to get list of holiday
def get_holiday(year, month):

    num_days = (datetime(year, month+1, 1) - datetime(year, month, 1)).days
    date_list = [datetime(year, month, day) for day in range(1, num_days+1)]

    if year != 2023:
        raise ValueError("Only support year 2023")

    # Check weekend
    weekend = [date.weekday() in [5, 6] for date in date_list]

    # Combine all holiday
    holiday = [weekend[i] or date_list[i] in thai_special_holiday for i in range(len(date_list))]

    return holiday

no_morn_con_date = [
    datetime(2023, 3, 1),
    datetime(2023, 3, 8),
    datetime(2023, 3, 15),
    datetime(2023, 3, 22),
    datetime(2023, 3, 29)]


# define get morning conference day
# TODO : input no_morn_con_date
def get_morn_con_day(year, month, no_morn_con_date=no_morn_con_date):
    num_days = (datetime(year, month+1, 1) - datetime(year, month, 1)).days
    date_list = [datetime(year, month, day) for day in range(1, num_days+1)]

    # Check weekend
    weekend = [date.weekday() in [5, 6] for date in date_list]

    # Check holiday
    holiday = [weekend[i] or date_list[i] in thai_special_holiday for i in range(len(date_list))]

    # Combine all holiday
    no_morn_con_day = [holiday[i] or date_list[i] in no_morn_con_date for i in range(len(date_list))]

    morn_con_day = [not no_morn_con_day[i] for i in range(len(date_list))]

    return morn_con_day

# print(get_morn_con_day(2023, 3))

    