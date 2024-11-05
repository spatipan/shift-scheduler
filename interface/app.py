import streamlit as st
import re
import json
import os
from modules.scheduler_app.app import SchedulerApp
from config import config_logging
import logging


CONFIG_PATH = 'config.json'

config_logging()

# Function to load config
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

# Function to save config
def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
        st.success("Configuration saved successfully!")


# Create tabs
tab1, tab2, tab3 = st.tabs(["Main","Setting", "Log", ])

# Cache the app
@st.cache_resource
def get_app():
    return SchedulerApp()

@st.cache_data
def get_config():
    return load_config()

config = get_config()
app = get_app()

# Content for "Setting" tab
with tab1:
    st.title("Main")

    # Button to run the main function
    if st.button("Fetch Information"):
        app.fetch_information()
        # events = app.calendar_app.events
        app._update_config()
        st.success("Information fetched successfully!")
        start = app.schedule.start
        end = app.schedule.end
        st.write(f"Start date: {start}")
        st.write(f"End date: {end}")
    
    if st.button("Solve Schedule"):
        app.solve()
        st.success("Schedule solved successfully!")
        app.update_information()

    if st.button("Visualize Schedule"):
        app.visualize()
        st.success("Schedule visualized successfully!")

    if st.button("Open Sheet"):
        # redirect to the google sheet in browser with id
        sheet_id = config['SPREADSHEET_ID']
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        st.write(f"Opening sheet: {sheet_url}")


    

# Content for "Setting" tab
with tab2:
    st.title("Setting")
    # Load config
    config = load_config()
    configurable = config['CONFIGURABLE']
    config_keys = configurable
    config_values = [config[key] for key in config_keys]

    # Display the config with input fields, and handle nested dict, list
    for i in range(len(config_keys)):
        if isinstance(config_values[i], dict):
            st.write(config_keys[i])
            for key, value in config_values[i].items():
                config_values[i][key] = st.text_input(key, value)
        elif isinstance(config_values[i], list):
            st.write(config_keys[i])
            for j in range(len(config_values[i])):
                config_values[i][j] = st.text_input(f'{config_keys[i]}_{j}', config_values[i][j])
        else:
            config[config_keys[i]] = st.text_input(config_keys[i], config_values[i])
            # separate line
            st.write('---')
    
    # Save the config
    if st.button("Save Config"):
        save_config(config)
        logging.info("Configuration saved successfully! with values: {}".format(config))


    # button to authorize google credentials
    # if st.button("Authorize Google Credentials"):
    #     app = SchedulerApp()
    #     st.write("Google credentials authorized")


# Content for "Log" tab
with tab3:
    logging_path = "tmp/logging.log"
    choices = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_level = st.multiselect("Log Level", choices, default = choices)

    # Write more beautiful log
    with open(logging_path, "r") as f:
        # Read the log file
        log = f.readlines()

        # Filter the log based on log level
        log = [line for line in log if any(re.search(level, line) for level in log_level)]

        # Display the log
        for line in log:
            st.write(line)


        
# import streamlit as st
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt


# def main():
#     st.title('My first app')
#     st.write('Here is our first attempt at using data to create a table:')
#     st.write(pd.DataFrame({
#         'first column': [1, 2, 3, 4],
#         'second column': [10, 20, 30, 40]
#     }))

#     """
#     # My first app
#     Here's our first attempt at using data to create a table:
#     """

#     df = pd.DataFrame({
#         'first column': [1, 2, 3, 4],
#         'second column': [10, 20, 30, 40]
#     })

#     df

#     """
#     Here's our first attempt at using data to create a line chart:
#     """

#     chart_data = pd.DataFrame(
#         np.random.randn(20, 3),
#         columns=['a', 'b', 'c'])

#     st.line_chart(chart_data)

#     """
#     Here's our first attempt at using data to create a map:
#     """

#     map_data = pd.DataFrame(
#         np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
#         columns=['lat', 'lon'])

#     st.map(map_data)

#     """
#     Here's our first attempt at using data to create a bar chart:
#     """

#     if st.checkbox('Show dataframe'):
#         chart_data = pd.DataFrame(
#             np.random.randn(50, 3),
#             columns=['a', 'b', 'c'])

#         st.line_chart(chart_data)

#     option = st.selectbox(
#         'Which number do you like best?',
#         df['first column'])

#     'You selected: ', option

#     left_column, right_column = st.columns(2)
#     pressed = left_column.button('Press me?')
#     if pressed:
#         right_column.write("Woohoo!")

#     expander = st.expander("FAQ")
#     expander.write("Here you could put in some really, really long explanations...")

#     st.write('Hello, *World!* :sunglasses:')


# if __name__ == '__main__':
#     main()

    