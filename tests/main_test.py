import unittest
from datetime import datetime
from modules.google_app import GoogleAppAuthenticator, CalendarApp
from modules.scheduler_app import ScheduleSolver, SchedulerSheetUI


import app
import config
import main


class TestApp(unittest.TestCase):
    def test_main(self):
        main.main()
        self.assertTrue(True)

    def test_config(self):
        config.config_logging()
        self.assertTrue(True)

    def test_google_app(self):
        authenticator = GoogleAppAuthenticator(SCOPES = config.GOOGLE_SCOPES)
        credentials = authenticator.authenticate(
            credentials = config.CREDENTIALS,
            token = config.TOKEN,
        )
        self.assertTrue(authenticator.authenticated)

    def test_scheduler_app(self):
        scheduler = ScheduleSolver()
        self.assertTrue(True)

    def test_calendar_app(self):
        calendar = CalendarApp()
        self.assertTrue(True)

    def test_get_value_from_json(self):
        path = config.SECRET_PATH
        key = 'credentials'
        subkey = ''
        value = config.get_value_from_json(path, key, subkey)
        self.assertTrue(value)
    
    # Test A1 notation to index (row, col)
    def test_a1_to_row_col(self):
        a1 = 'A1'
        row, col = SchedulerSheetUI.a1_to_index(a1)
        self.assertEqual(row, 0)
        self.assertEqual(col, 0)

        a1 = 'B2'
        row, col = SchedulerSheetUI.a1_to_index(a1)
        self.assertEqual(row, 1)
        self.assertEqual(col, 1)

        

    

if __name__ == '__main__':
    unittest.main()

