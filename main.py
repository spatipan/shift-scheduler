from modules.scheduler_app import SchedulerApp


from datetime import datetime
import config
import logging
# from app import App

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
    

    

