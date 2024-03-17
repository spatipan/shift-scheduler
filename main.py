
# from pkgs.google_app import GoogleAppAuthenticator, CalendarApp
# from pkgs.scheduler_app import *
from modules.scheduler_app.models.models import Event, Task, Employee, Shift, Schedule
from modules.scheduler_app.solver import ScheduleSolver, SchedulerConstraint, SchedulerConstraintGroup
from modules.scheduler_app import SchedulerApp
from modules.google_app import GoogleAppAuthenticator, CalendarApp, GoogleSheetApp

from datetime import datetime
import config
import logging
from app import App

def main() -> None:
    
    config.config_logging()

    app = SchedulerApp()
    app.fetch_information()
    app.solve()
    app.schedule.summary()
    app.visualize()
    app.update_information()



if __name__ == '__main__':
    main()
    

    

