from datetime import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
from google.auth.external_account_authorized_user import Credentials as ExternalAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging


# Google Sheet app - as UI for schedule
class GoogleSheetApp:
    def __init__(self, credentials: dict | Credentials | ExternalAccountCredentials | None = None):
        self.credentials = credentials
        self.service = None
        self.logger = logging.getLogger(__class__.__name__)
        if credentials is not None:
            self.initialize()

    def initialize(self) -> None:
        '''Initialize google sheet service'''
        try:
            self.service = build('sheets', 'v4', credentials=self.credentials)
            self.logger.debug('Service initialized successfully')
        except Exception as e:
            print(f'Error initializing service: {e}')
            self.logger.error(f'Error initializing service: {e}')

    # Convert respond to dictionary
    @staticmethod
    def convert_to_dict(respond):
        '''Converts the respond to dictionary'''
        header = respond[0]
        values = respond[1:]
        result = [dict(zip(header, value)) for value in values]
        return result

    # Read
    def read(self, spreadsheetId: str, sheetName: str, range: str) -> list[list]:
        '''Reads the sheet values, return as list of list'''
        assert self.service is not None, 'Service not initialized'

        # Call the Sheets API
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheetId, range= sheetName + '!' + range).execute()
        values = result.get('values', [])
        return values
    
    # Read as dictionary
    def read_as_dict(self, spreadsheetId: str, sheetName: str, range: str) -> list[dict]:
        '''Reads the sheet values, return as list of dictionary'''
        return self.convert_to_dict(self.read(spreadsheetId = spreadsheetId, sheetName = sheetName, range = range))
            
            
    def update(self, spreadsheetId: str, sheetName: str, range: str, values: list[list]) -> None:
        '''Updates the sheet values'''
        assert self.service is not None, 'Service not initialized'

        # Call the Sheets API
        try: 
            sheet = self.service.spreadsheets()
            body = {
                'values': values
            }
            result = sheet.values().update(spreadsheetId=spreadsheetId, range= sheetName + '!' + range, valueInputOption='RAW', body=body).execute()
            self.logger.debug(f'{result.get("updatedCells")} cells updated')
        except HttpError as e:
            self.logger.error(f'Error updating sheet: {e}')
            
        return result

    # TODO: Add create, update, delete methods
