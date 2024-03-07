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
    def __init__(self, credentials: Credentials | ExternalAccountCredentials | None = None):
        self.credentials = credentials
        self.service = None
        self.logger = logging.getLogger(__class__.__name__)
        self.service = self.initialize()

    def initialize(self):
        '''Initialize google sheet service'''
        try:
            self.service = build('sheets', 'v4', credentials=self.credentials)
            self.logger.debug('Service initialized successfully')
        except Exception as e:
            print(f'Error initializing service: {e}')
            self.service = None
            self.logger.error(f'Error initializing service: {e}')
      
