from datetime import datetime
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials 
from google.auth.external_account_authorized_user import Credentials as ExternalAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
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
                if creds and creds.expired and creds.refresh_token:
                    try:
                        self.logger.debug('Refreshing expired credentials...')
                        creds.refresh(Request())
                        self.logger.debug('Credentials refreshed successfully')
                    except RefreshError:
                        st.warning("Token expired or revoked. Please re-authenticate.")
                        self._handle_reauthentication_flow()
                else:
                    st.warning("No valid token found. Re-authentication is required.")
                    self._handle_reauthentication_flow()

        except RefreshError as e:
            self.logger.error("RefreshError encountered: Token has expired or been revoked.")
            st.error("Token has been expired or revoked. Please re-authenticate.")
            self._handle_reauthentication_flow()

        except Exception as e:
            self.logger.error(f'Error during authentication: {e}')
            raise ValueError(f'Error during authentication: {e}')
            
        self._save_credentials(creds)
        self.credentials = creds
        self.authenticated = True
        return self.credentials

    def _handle_reauthentication_flow(self):
        """Handle re-authentication flow for Streamlit."""
        self.logger.debug('Deleting token...')
        self._delete_token()
        self.logger.debug('Starting re-authentication flow...')
        flow = InstalledAppFlow.from_client_config(self.credentials, self.SCOPES)
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f"[Click here to authorize]({auth_url})")
        auth_code = st.text_input("Paste the authorization code here:")

        if auth_code:
            try:
                creds = flow.fetch_token(code=auth_code)
                st.success("Authentication successful!")
                self._save_credentials(creds)
                self.credentials = creds
            except Exception as e:
                st.error(f"Failed to fetch token: {e}")
                self.logger.error(f"Error fetching token: {e}")
    
    def _save_credentials(self, creds):
        '''Save credentials to a file'''
        with open(SECRET_PATH, "r") as file:
            secret = json.load(file)
            secret['token'] = json.loads(creds.to_json())

        with open(SECRET_PATH, "w") as file:
            json.dump(secret, file)
            self.logger.debug('Credentials saved to file')

    ##TODO: Function to delete token from secret file   
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

