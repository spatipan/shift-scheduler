from datetime import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
from google.auth.external_account_authorized_user import Credentials as ExternalAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import json

from config import SECRET_PATH



# GoogleCloud app
class GoogleAppAuthenticator:
    def __init__(self, SCOPES: list = ['https://www.googleapis.com/auth/calendar.readonly', 
                                      'https://www.googleapis.com/auth/spreadsheets.readonly']):
        self.credentials = None
        self.token = None
        self.authenticated = False
        self.service = None
        self.SCOPES = SCOPES
        self.logger = logging.getLogger(__class__.__name__)

    def authenticate(self, credentials: dict,
                     token: dict | None = None,):
        '''Authenticate user to use google services'''
        if self.authenticated:
            self.logger.debug('User already authenticated')
            return self.credentials 
        
        self.logger.debug('Authenticating user ...')
        self.credentials = credentials
        self.token = token

        try:
            creds = None
            if self.token:
                self.logger.debug('Loading credentials from file')
                creds = Credentials.from_authorized_user_info(self.token, self.SCOPES)
                self.logger.debug('Credentials loaded from file')
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.logger.debug('Credentials refreshed')
                else:
                    flow = InstalledAppFlow.from_client_config(self.credentials, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    self.logger.debug('Credentials generated')
                    # Save the credentials for the next run
                with open(SECRET_PATH, "r") as file:
                    secret = json.load(file)
                    secret['token'] = json.loads(creds.to_json())
                    secret_json = json.dumps(secret)

                with open(SECRET_PATH, "w") as file:
                    file.write(secret_json)
                    self.logger.debug('Credentials saved to file')

            self.credentials = creds
            self.authenticated = True
        except Exception as e:
            print(f'Error authenticating user: {e}')
            self.logger.error(f'Error authenticating user: {e}')

        return self.credentials


