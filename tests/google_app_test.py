import unittest

from modules.google_app import GoogleAppAuthenticator, CalendarApp, GoogleSheetApp
import config
from datetime import datetime

class TestApp(unittest.TestCase):

    def test_google_app(self):
        authenticator = GoogleAppAuthenticator(SCOPES = config.GOOGLE_SCOPES)
        credentials = authenticator.authenticate(
            credentials = config.CREDENTIALS,
            token = config.TOKEN,
        )
        self.assertTrue(authenticator.authenticated)

    def test_calendar_app(self):
        authenticator = GoogleAppAuthenticator(SCOPES = config.GOOGLE_SCOPES)
        credentials = authenticator.authenticate(
            credentials = config.CREDENTIALS,
            token = config.TOKEN,
        )
        calendar = CalendarApp(credentials)
        # check if service is not None
        self.assertTrue(calendar.service)

        # fetch events from calendar
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        events = calendar.read(calendarId=config.CALENDAR_ID, start=start, end=end)
        self.assertTrue(events)

    def test_sheet_app(self):
        authenticator = GoogleAppAuthenticator(SCOPES = config.GOOGLE_SCOPES)
        credentials = authenticator.authenticate(
            credentials = config.CREDENTIALS,
            token = config.TOKEN,
        )
        sheet = GoogleSheetApp(credentials)
        self.assertTrue(sheet.service)

        #fetch values from sheet
        values = sheet.read(spreadsheetId=config.SPREADSHEET_ID, sheetName=config.SHEET_NAME, range='A1:Z100')
        self.assertTrue(values)



   