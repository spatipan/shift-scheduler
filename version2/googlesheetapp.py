import gspread
import regex as re


class GoogleSheetApp():
    def __init__(self):
        self.service = gspread.service_account(filename="creds.json") #type: ignore

    def get_sheet_values(self, spreadsheet_id, range, type = 'values'):
        sheet = self.service.open_by_key(spreadsheet_id)

        SHEET_NAME = re.split(r'!', range)[0].strip()
        RANGE_NAME = re.split(r'!', range)[1].strip()
        worksheet = sheet.worksheet(SHEET_NAME)
        values = worksheet.get_values(RANGE_NAME)
        if type == 'values':
            return values
        elif type == 'dict':
            titles = values[0]
            values = values[1:]
            result = [dict(zip(titles, value)) for value in values]
            return result
    
    def update_sheet_values(self, spreadsheet_id, range, values):
        sheet = self.service.open_by_key(spreadsheet_id)

        SHEET_NAME = re.split(r'!', range)[0].strip()
        RANGE_NAME = re.split(r'!', range)[1].strip()
        worksheet = sheet.worksheet(SHEET_NAME)
        worksheet.update(RANGE_NAME, values)

        print(f'Updated {spreadsheet_id} {range} with {values}')

    def clear_sheet(self, spreadsheet_id, sheet_name):
        sheet = self.service.open_by_key(spreadsheet_id)
        worksheet = sheet.worksheet(sheet_name)
        worksheet.clear()


if __name__ == '__main__':

    KEY = "1wHNERHZUxl8mI7xOPtWsvRBHxw9r_ohFoi7BWET_YdU"
    RANGE = "Interface demo! A1"

    app = GoogleSheetApp()

    values = app.get_sheet_values(KEY, RANGE)

    new_title = "New Title"

    app.update_sheet_values(KEY, RANGE, new_title)

    print(values)



# create requirements.txt with conda
# conda list -e > requirements.txt