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

from config import CREDS_PATH, TOKEN_PATH

# GoogleCloud app
class GoogleAppAuthenticator:
    def __init__(self, credentials_path: str, token_path: str, scopes: list):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes
        self.logger = logging.getLogger(self.__class__.__name__)
        self.credentials = self.authenticate()


    def authenticate(self):
        """Authenticate the user using credentials and token files."""
        creds = None

        # Try loading existing token
        if os.path.exists(self.token_path):
            try:
                self.logger.debug('Attempting to load credentials from token file')
                with open(self.token_path, 'r') as token_file:
                    token_info = json.load(token_file)
                    creds = Credentials.from_authorized_user_info(token_info, self.scopes)
                
                if creds.valid:
                    self.logger.info('Loaded valid credentials from token file.')
                elif creds.expired and creds.refresh_token:
                    self.logger.info('Credentials expired. Refreshing...')
                    creds.refresh(Request())
                    self._save_credentials(creds)
                else:
                    self.logger.warning('Credentials invalid or expired without refresh token.')
                    creds = None
            except:
                self.logger.info('Token file not found or invalid.')

            if not creds or not creds.valid:
                creds = self.authenticate_user()

            self.credentials = creds

            return self.credentials
        
    def authenticate_user(self):
        """Initiate OAuth2 authentication flow."""
        self.logger.info('Initiating OAuth2 user authentication flow.')
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path, self.scopes
        )
        creds = flow.run_local_server(port=0)
        self._save_credentials(creds) # type: ignore
        return creds
    
    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file."""
        token_info = json.loads(creds.to_json())
        with open(self.token_path, 'w') as token_file:
            json.dump(token_info, token_file, indent=4)
        self.logger.info('Saved credentials to token file.')

    def delete_token(self):
        """Delete existing token."""
        try:
            os.remove(self.token_path)
            self.logger.info('Deleted token file successfully.')
        except FileNotFoundError:
            self.logger.warning('Token file not found. Nothing to delete.')
        except Exception as e:
            self.logger.error(f'Error deleting token file: {e}')
            raise
      
import logging
from config import CREDS_PATH, TOKEN_PATH, GOOGLE_SCOPES

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    authenticator = GoogleAppAuthenticator(
        credentials_path=CREDS_PATH,
        token_path=TOKEN_PATH,
        scopes=GOOGLE_SCOPES
    )

    credentials = authenticator.authenticate()

    # Example usage: Google Calendar API
    try:
        service = build('calendar', 'v3', credentials=credentials)
        events = service.events().list(calendarId='primary').execute()
        print(events)
    except HttpError as e:
        logging.error(f'HTTP error occurred: {e}')

