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

from config import CREDENTIALS, TOKEN



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
            # Load credentials from token
            creds = None
            if self.token:
                self.logger.debug('Loading credentials from token')
                creds = Credentials.from_authorized_user_info(self.token, self.SCOPES)

            if creds and creds.valid and not creds.expired:
                self.logger.debug('Credentials are valid')
            else:
                self.logger.debug(f'Credentials are not valid')
                self.logger.debug('Generating new credentials...')
                flow = InstalledAppFlow.from_client_config(self.credentials, self.SCOPES)
                creds = flow.run_local_server(port=0)
                self.logger.debug('New credentials generated')


        except Exception as e:
            self.logger.error(f'Error during authentication: {e}')
            raise ValueError(f'Error during authentication: {e}')
            
        self.credentials = creds
        self.authenticated = True
        return self.credentials
    
 
if __name__ == '__main__':
    authenticator = GoogleAppAuthenticator()
    credentials = authenticator.authenticate(
        credentials = CREDENTIALS,
        token = TOKEN,
    )

