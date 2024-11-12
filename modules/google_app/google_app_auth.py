from datetime import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
from google.auth.exceptions import RefreshError
import logging
import json

from config import SECRET_PATH, CREDENTIALS, TOKEN

class GoogleAppAuthenticator:
    def __init__(self, SCOPES: list = ['https://www.googleapis.com/auth/calendar.readonly', 
                                      'https://www.googleapis.com/auth/spreadsheets.readonly']):
        self.credentials = None
        self.token = None
        self.authenticated = False
        self.SCOPES = SCOPES
        self.logger = logging.getLogger(__class__.__name__)

    def authenticate(self, credentials: dict, token: dict | None = None):
        '''Authenticate user to use Google services'''
        if self.authenticated:
            self.logger.debug('User already authenticated')
            return self.credentials 
        
        self.logger.debug('Authenticating user ...')
        self.credentials = credentials
        self.token = token

        try:
            creds = None
            if self.token:
                self.logger.debug('Loading credentials from token')
                creds = Credentials.from_authorized_user_info(self.token, self.SCOPES)

            if creds and creds.valid and not creds.expired:
                self.logger.debug('Credentials are valid')
            else:
                if creds and creds.expired:
                    if creds.refresh_token:
                        try:
                            self.logger.debug('Refreshing expired credentials...')
                            creds.refresh(Request())
                            self.logger.debug('Credentials refreshed successfully')
                        except RefreshError:
                            self.logger.error("Token refresh failed: Token expired or revoked. Re-authentication required.")
                            raise ValueError("Token refresh failed: Token expired or revoked.")
                    else:
                        self.logger.error("No refresh token available. Re-authentication required.")
                        raise ValueError("No refresh token available. Re-authentication required.")
                else:
                    self.logger.error("Invalid or expired credentials without a refresh token.")
                    raise ValueError("Re-authentication required due to invalid or expired credentials.")

        except RefreshError as e:
            self.logger.error("RefreshError encountered: Token has expired or been revoked.")
            raise ValueError("Token has been expired or revoked. Please re-authenticate.")

        except Exception as e:
            self.logger.error(f'Error during authentication: {e}')
            raise ValueError(f'Error during authentication: {e}')
            
        self._save_credentials(creds)
        self.credentials = creds
        self.authenticated = True
        return self.credentials


    def _save_credentials(self, creds):
        '''Save credentials to a file'''
        with open(SECRET_PATH, "r") as file:
            secret = json.load(file)
            secret['token'] = json.loads(creds.to_json())

        with open(SECRET_PATH, "w") as file:
            json.dump(secret, file)
            self.logger.debug('Credentials saved to file')

    ## Function to delete token from secret file   
    def _delete_token(self):
        '''Delete token from secret file'''
        with open(SECRET_PATH, "r") as file:
            secret = json.load(file)
            secret['token'] = None

        with open(SECRET_PATH, "w") as file:
            json.dump(secret, file)
            self.logger.debug('Token deleted from file')

if __name__ == '__main__':
    authenticator = GoogleAppAuthenticator()
    credentials = authenticator.authenticate(
        credentials = CREDENTIALS,
        token = TOKEN,
    )
