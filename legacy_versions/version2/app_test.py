import streamlit as st
from datetime import datetime
import pandas as pd

from scheduler import schedule_shifts

st.set_page_config(
    page_title="EM CMU Staff Shift scheduling app",
    page_icon=":sunglasses:",
)

st.title("EM CMU Staff Shift scheduling app")
st.write("This app is for scheduling staff shifts for the EM CMU ")

# =================== Session state =================== #
if 'year' not in st.session_state: st.session_state.year = 2024
if 'month' not in st.session_state: st.session_state.month = 'January'
if 'numbers' not in st.session_state: st.session_state.numbers = 11
for i in range(st.session_state.numbers):
    if f'staff_name{i}' not in st.session_state: st.session_state[f'staff_name{i}'] = f'Staff name{i}'


# =================== Layouts =================== #

main_tab, settings_tab = st.tabs(['Main', 'Settings'])


# =================== Settings tab =================== #

settings_tab.subheader('Shift settings')
st.session_state.numbers = settings_tab.number_input('Number of staff', min_value=1, max_value=20, value=1, step=1)
st.session_state.month = settings_tab.selectbox('Month', ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
st.session_state.year = settings_tab.selectbox('Year', [2023, 2024, 2025])

with settings_tab.expander("Advanced settings"):
    with st.form("staff_name_form"):
        st.write("Staff names")
        staff_name = {}
        for i in range(st.session_state.numbers):
            staff_name[i] = st.text_input(f'staff_name{i}', value=st.session_state[f'staff_name{i}'])
            # st.session_state.staff_name = st.text_input('me', value=st.session_state.staff_name)
        submit_button = st.form_submit_button(label='Apply')

        if submit_button:
            for i in range(st.session_state.numbers):
                st.session_state[f'staff_name{i}'] = staff_name[i]
         
 
# =================== Main tab =================== #

main_tab.subheader('Shifts')

if main_tab.button('Generate shifts'):
    # loading
    with st.spinner('Generating shifts...'):
        solution_printer = schedule_shifts()
        df = solution_printer.get_solution()
        workload = solution_printer.workloads()
    main_tab.dataframe(df)
    main_tab.write(workload)


