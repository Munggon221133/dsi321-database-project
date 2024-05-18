import streamlit as st
import pandas as pd
import psycopg2
import toml
from streamlit_option_menu import option_menu
import about as about
import visualization as visualization
import allData as all_data
import masterData as master_data
import tranData as tran_data
import refData as ref_data

st.set_page_config(
    page_title="Your App Name",
)

selected = option_menu(
    menu_title=None,
    options=["Data", "Visualization", "About"],
    icons=["database", "bar-chart", "people-fill"],
    default_index=0,
    orientation="horizontal"
)

if selected == "Data":
    data_option = st.selectbox("Select the types of data you want to explore.", ["All Data", "Master Data", "Transaction Activity Data", "Reference Data"])
    if data_option == "All Data":
        all_data.app()
    elif data_option == "Master Data":
        master_data.app()
    elif data_option == "Transaction Activity Data":
        tran_data.app()
    elif data_option == "Reference Data":
        ref_data.app()
elif selected == "Visualization":
    visualization.app()
elif selected == "About":
    about.app()