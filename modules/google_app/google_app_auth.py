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

# from config import SECRET_PATH, CREDENTIALS, TOKEN


import json
import logging
import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

class GoogleAppAuthenticator:
    def __init__(self, SCOPES: list = ['https://www.googleapis.com/auth/calendar.readonly', 
                                      'https://www.googleapis.com/auth/spreadsheets.readonly']):
        self.credentials = None
        self.token = None
        self.client_secrets = None
        self.authenticated = False
        self.SCOPES = SCOPES
        self.logger = logging.getLogger(__class__.__name__)

    def authenticate(self):
        '''Authenticate user to use Google services'''
        if self.authenticated:
            self.logger.debug('User already authenticated')
            return self.credentials
        
        self.logger.debug('Authenticating user ...')

        # Load client secrets from Streamlit secrets
        try:
            self.client_secrets = json.loads(st.secrets["google_oauth"]["client_secrets"])
            token_data = json.loads(st.secrets["google_oauth"].get("token", "{}"))
        except KeyError as e:
            self.logger.error(f'Missing key in secrets: {e}')
            raise ValueError(f'Missing key in secrets: {e}')
        
        # Create credentials from existing token data if available
        if token_data:
            creds = Credentials.from_authorized_user_info(token_data, scopes=self.SCOPES)
            self.logger.debug('Credentials loaded from existing token data')
        else:
            creds = None
        
        # Refresh credentials if expired or create new credentials if none exist
        try:
            if creds and creds.expired and creds.refresh_token:
                self.logger.debug('Refreshing expired credentials...')
                creds.refresh(Request())
                self.logger.debug('Credentials refreshed successfully')
            elif not creds:
                # Authenticate using the client secrets for a new token
                with open("temp_client_secrets.json", "w") as temp_file:
                    json.dump(self.client_secrets, temp_file)
                flow = InstalledAppFlow.from_client_secrets_file("temp_client_secrets.json", scopes=self.SCOPES)
                creds = flow.run_console()
                self.logger.debug('New credentials generated')
        except Exception as e:
            self.logger.error(f'Error during authentication: {e}')
            raise ValueError(f'Error during authentication: {e}')

        # Save credentials if authenticated successfully
        if creds:
            self._save_credentials(creds)
            self.credentials = creds
            self.authenticated = True
            return self.credentials

    def _save_credentials(self, creds):
        '''Save credentials to a file'''
        new_token_data = json.loads(creds.to_json())
        with open('updated_token.json', 'w') as token_file:
            json.dump(new_token_data, token_file)
        self.logger.debug('Updated credentials saved to file')



# # GoogleCloud app
# class GoogleAppAuthenticator:
#     def __init__(self, SCOPES: list = ['https://www.googleapis.com/auth/calendar.readonly', 
#                                       'https://www.googleapis.com/auth/spreadsheets.readonly']):
#         self.credentials = None
#         self.token = None
#         self.client_secrets = None
#         self.authenticated = False
#         self.service = None
#         self.SCOPES = SCOPES
#         self.logger = logging.getLogger(__class__.__name__)

#     def authenticate_from_client_secrets(self, client_secrets: dict)
#         '''Authenticate user to use google services'''
#         if self.authenticated:
#             self.logger.debug('User already authenticated')
#             return self.credentials
#         self.logger.debug('Authenticating user ...')
#         self.client_secrets = client_secrets
#         try:
#             if self.client_secrets:
#                 # Use the client secrets for OAuth flow
#                 flow = InstalledAppFlow.from_client_secrets_file("temp_client_secrets.json", scopes=self.SCOPES)
#                 creds = flow.run_local_server(port=0)
#                 self.logger.debug('New credentials generated')
#         except Exception as e:
#             self.logger.error(f'Error during authentication: {e}')
#             raise ValueError(f'Error during authentication: {e}')

#         self._save_credentials(creds)
#         self.credentials = creds
#         self.authenticated = True
#         return self.credentials

#     # def authenticate(self, credentials: dict,
#     #                  token: dict | None = None,):
#     #     '''Authenticate user to use google services'''
#     #     if self.authenticated:
#     #         self.logger.debug('User already authenticated')
#     #         return self.credentials 
        
#     #     self.logger.debug('Authenticating user ...')
#     #     self.credentials = credentials
#     #     self.token = token


#     #     try:
#     #         # Load credentials from token
#     #         creds = None
#     #         if self.token:
#     #             self.logger.debug('Loading credentials from token')
#     #             creds = Credentials.from_authorized_user_info(self.token, self.SCOPES)

#     #         if creds and creds.valid and not creds.expired:
#     #             self.logger.debug('Credentials are valid')
#     #         else:
#     #             self.logger.debug(f'Credentials are not valid')

#     #             self.logger.debug('Deleting token...')
#     #             self._delete_token()
#     #             self.logger.debug('Generating new credentials...')
#     #             flow = InstalledAppFlow.from_client_config(self.credentials, self.SCOPES)
#     #             creds = flow.run_console()
#     #             self.logger.debug('New credentials generated')


#     #     except Exception as e:
#     #         self.logger.error(f'Error during authentication: {e}')
#     #         raise ValueError(f'Error during authentication: {e}')
            
#     #     self._save_credentials(creds)
#     #     self.credentials = creds
#     #     self.authenticated = True
#     #     return self.credentials
    
#     def _save_credentials(self, creds):
#         '''Save credentials to a file'''
#         with open(SECRET_PATH, "r") as file:
#             secret = json.load(file)
#             secret['token'] = json.loads(creds.to_json())

#         with open(SECRET_PATH, "w") as file:
#             json.dump(secret, file)
#             self.logger.debug('Credentials saved to file')

#     ##TODO: Function to delete token from secret file   
#     def _delete_token(self):
#         '''Delete token from secret file'''
#         with open(SECRET_PATH, "r") as file:
#             secret = json.load(file)
#             secret['token'] = None

#         with open(SECRET_PATH, "w") as file:
#             json.dump(secret, file)
#             self.logger.debug('Token deleted from file')
      


if __name__ == '__main__':
    authenticator = GoogleAppAuthenticator()
    credentials = authenticator.authenticate(
        credentials = CREDENTIALS,
        token = TOKEN,
    )

