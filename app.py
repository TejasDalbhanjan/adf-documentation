import streamlit as st
import json
import pandas as pd
import plotly.express as px

from parser.pipeline_parser import (
    extract_pipeline_name,
    extract_pipeline_parameters,
    extract_activities
)

from graphs.dependancy_graph import (
    generate_dependency_graph
)

from reports.excel_report import (
    create_excel_report
)

# -----------------------------------
# Page Config
# -----------------------------------

st.set_page_config(
    page_title="ADF Pipeline Analyzer",
    layout="wide"
)

# -----------------------------------
# Title
# -----------------------------------

st.title("ADF Pipeline Analyzer")

# -----------------------------------
# File Upload
# -----------------------------------

uploaded_file = st.file_uploader(
    "Upload ADF Pipeline JSON",
    type=["json"]
)

if uploaded_file:

    # -----------------------------------
    # Load JSON
    # -----------------------------------

    data = json.load(uploaded_file)

    # -----------------------------------
    # Pipeline Name
    # -----------------------------------

    pipeline_name = extract_pipeline_name(
        data
    )

    st.header(
        f"Pipeline: {pipeline_name}"
    )

    # -----------------------------------
    # Pipeline Parameters
    # -----------------------------------

    pipeline_parameters = (
        extract_pipeline_parameters(
            data
        )
    )

    st.subheader(
        "Pipeline Parameters"
    )

    if pipeline_parameters:

        st.json(
            pipeline_parameters
        )

    else:

        st.info(
            "No Parameters Found"
        )

    # -----------------------------------
    # Extract Activities
    # -----------------------------------

    activities = extract_activities(
        data
    )

    # -----------------------------------
    # Summary Metrics
    # -----------------------------------

    st.subheader(
        "Pipeline Summary"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Activities",
            len(activities)
        )

    with col2:

        unique_types = len(
            set(
                activity["type"]
                for activity in activities
            )
        )

        st.metric(
            "Activity Types",
            unique_types
        )

    with col3:

        dependency_count = sum(
            len(activity["depends_on"])
            for activity in activities
        )

        st.metric(
            "Dependencies",
            dependency_count
        )

    # -----------------------------------
    # Activities Table
    # -----------------------------------

    st.subheader(
        "Activities"
    )

    rows = []

    for activity in activities:

        depends = []

        for dep in activity["depends_on"]:

            depends.append(
                dep["activity"]
            )

        rows.append({

            "Activity Name":
                activity["name"],

            "Type":
                activity["type"],

            "Parent":
                activity["parent"],

            "Depends On":
                ",".join([
                    dep["activity"]
                    for dep in activity["depends_on"]
                ]),

            "Datasets":
                ",".join(
                    activity["datasets"]
                ),

            "Linked Services":
                ",".join(
                    activity["linked_services"]
                ),

            "Dataflows":
                ",".join(
                    activity["dataflows"]
                ),

            "Pipelines":
                ",".join(
                    activity["pipelines"]
                ),

            "Parameters":
                str(
                    activity["parameters"]
                )
        })

    activities_df = pd.DataFrame(rows)

    st.dataframe(
        activities_df,
        width="stretch"
    )

    # -----------------------------------
    # Activity Distribution
    # -----------------------------------

    st.subheader(
        "Activity Distribution"
    )

    chart = px.histogram(
        activities_df,
        x="Type"
    )

    st.plotly_chart(
        chart,
        width="stretch"
    )

    # -----------------------------------
    # Datasets
    # -----------------------------------

    st.subheader(
        "Datasets"
    )

    dataset_rows = []

    for activity in activities:

        for dataset in activity["datasets"]:

            dataset_rows.append({

                "Activity":
                    activity["name"],

                "Dataset":
                    dataset
            })

    if dataset_rows:

        datasets_df = pd.DataFrame(
            dataset_rows
        )

        st.dataframe(
            datasets_df,
            width="stretch"
        )

    else:

        st.info(
            "No Datasets Found"
        )

    # -----------------------------------
    # Dependency Graph
    # -----------------------------------

    st.subheader(
        "Dependency Graph"
    )

    graph = generate_dependency_graph(
        activities
    )

    st.graphviz_chart(graph)

    # -----------------------------------
    # Excel Export
    # -----------------------------------

    st.subheader(
        "Export Report"
    )

    excel_path = create_excel_report(
        activities,
        pipeline_name
    )

    with open(
        excel_path,
        "rb"
    ) as file:

        st.download_button(

            label="Download Excel Report",

            data=file,

            file_name=(
                f"{pipeline_name}_report.xlsx"
            )
        )