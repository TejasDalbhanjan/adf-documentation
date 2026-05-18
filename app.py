import streamlit as st 
import json

st.title("ADF Pipeline Analyzer")

uploaded_file = st.file_uploader("upload ADF json")


if uploaded_file:
    data = json.load(uploaded_file)
    pipeline_name = data['name']
    st.header(f"Pipeline Name: {pipeline_name}")
    activities = data['properties']['activities']

    for activity in activities:
        st.write(
            f"Activity: {activity['name']} | Type: {activity['type']}"
        )
    st.success("File Uploaded successfully")