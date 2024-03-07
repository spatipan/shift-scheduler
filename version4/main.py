
from pkgs.google_app import GoogleAppAuthenticator, CalendarApp
from pkgs.scheduler_app import *
from config import *
import logging

def main() -> None:
    config_logging()

    # authenticate user
    authenticator = GoogleAppAuthenticator(SCOPES = GOOGLE_SCOPES)
    credentials = authenticator.authenticate(
        credentials = CREDENTIALS,
        token = TOKEN,
    )



if __name__ == '__main__':
    main()
    

    

