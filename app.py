import streamlit as st 
import json
import pandas as pd

from parser.pipeline_parser import extract_activities

st.set_page_config(page_title="ADF Pipeline Analyzer", page_icon=":bar_chart:", layout="wide")

st.title("ADF Pipeline Analyzer")

uploaded_file = st.file_uploader("upload ADF json", type=["json"])



if uploaded_file:
    
    data = json.load(uploaded_file)
    
    pipeline_name = data['name']
    
    st.header(f"Pipeline Name: {pipeline_name}")
    
    activities = extract_activities(data)

    st.subheader("Activities")
    
    for activity in activities:
        st.write(
            f"Activity: {activity['name']} | Type: {activity['type']}"
        )
    st.success("File Uploaded successfully")