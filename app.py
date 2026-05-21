import streamlit as st
import json
import pandas as pd
import plotly.express as px


from reports.word_report import (
    create_word_report
)

from parser.pipeline_parser import (
    extract_pipeline_name,
    extract_pipeline_parameters,
    extract_pipeline_variables,
    extract_activities
)
from parser.arm_template_parser import (
    is_arm_template,
    extract_pipelines_from_arm
)

from graphs.dependancy_graph import (
    generate_dependency_graph
)

from graphs.lineage_graph import (
    generate_lineage_graph
)

from reports.excel_report import (
    create_excel_report
)

from lineage.lineage_builder import (
    build_dataset_lineage
)

from lineage.impact_analysis import (
    build_impact_analysis
)

from governance.optimization_engine import (
    generate_optimization_recommendations
)

# -----------------------------------
# Page Config
# -----------------------------------

st.set_page_config(

    page_title="Enterprise ADF Analyzer",

    layout="wide"
)

# -----------------------------------
# Title
# -----------------------------------

st.title(
    "Enterprise ADF Pipeline Analyzer"
)

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

    data = json.load(
        uploaded_file
    )

    # -----------------------------------
    # Support Single Pipeline + ARM
    # -----------------------------------

    pipelines = []

    if is_arm_template(data):

        st.success(
            "ARM Template Detected"
        )

        pipelines = (
            extract_pipelines_from_arm(
                data
            )
        )

    else:

        st.success(
            "Single Pipeline JSON Detected"
        )

        pipelines = [data]

    # -----------------------------------
    # Loop Through Pipelines
    # -----------------------------------

    for pipeline_data in pipelines:

        # -----------------------------------
        # Pipeline Name
        # -----------------------------------

        pipeline_name = extract_pipeline_name(
            pipeline_data,
            full_data=data
        )

        st.header(
            f"Pipeline: {pipeline_name}"
        )

        # -----------------------------------
        # Pipeline Parameters
        # -----------------------------------

        # -----------------------------------
        # Pipeline Parameters & Variables
        # -----------------------------------

        colA, colB = st.columns(2)

        with colA:
            st.subheader("Pipeline Parameters")
            pipeline_parameters = extract_pipeline_parameters(pipeline_data)
            
            if pipeline_parameters:
                st.json(pipeline_parameters)
            else:
                st.info("No Parameters Found")

        with colB:
            st.subheader("Pipeline Variables")
            pipeline_variables = extract_pipeline_variables(pipeline_data)
            
            if pipeline_variables:
                st.json(pipeline_variables)
            else:
                st.info("No Variables Found")

        # -----------------------------------
        # Extract Activities
        # -----------------------------------

        activities = extract_activities(
            pipeline_data,
            full_data=data
        )

        # -----------------------------------
        # Build Lineage
        # -----------------------------------

        lineage = build_dataset_lineage(
            activities
        )

        # -----------------------------------
        # Impact Analysis
        # -----------------------------------

        impact_analysis = (
            build_impact_analysis(
                activities
            )
        )

        # -----------------------------------
        # Optimization
        # -----------------------------------

        optimization = (
            generate_optimization_recommendations(
                activities
            )
        )

        # -----------------------------------
        # Summary Metrics
        # -----------------------------------

        st.subheader(
            "Pipeline Summary"
        )

        col1, col2, col3, col4 = st.columns(4)

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

        with col4:

            dataset_count = len(

                set(

                    dataset

                    for activity in activities

                    for dataset in activity[
                        "datasets"
                    ]
                )
            )

            st.metric(

                "Datasets",

                dataset_count
            )

        # -----------------------------------
        # Activities Table
        # -----------------------------------

        st.subheader(
            "Activities"
        )

        rows = []

        for activity in activities:
            depends_formatted = []
            for dep in activity["depends_on"]:
                conds = dep.get("conditions", [])
                if conds:
                    depends_formatted.append(f"{dep['activity']} ({', '.join(conds)})")
                else:
                    depends_formatted.append(dep['activity'])
            rows.append({

                "Activity Name":
                    activity["name"],

                "Type":
                    activity["type"],

                "Parent":
                    activity["parent"]
                    if activity["parent"]
                    else "NA",

                "Depends On":
                    ",\n".join(depends_formatted) if depends_formatted else "NA",

                "Datasets":
                    ",".join(
                        activity["datasets"]
                    )
                    if activity["datasets"]
                    else "NA",

                "Linked Services":
                    ",".join(
                        activity[
                            "linked_services"
                        ]
                    )
                    if activity[
                        "linked_services"
                    ]
                    else "NA",

                "Dataflows":
                    ",".join(
                        activity["dataflows"]
                    )
                    if activity["dataflows"]
                    else "NA",

                "Pipelines":
                    ",".join(
                        activity["pipelines"]
                    )
                    if activity["pipelines"]
                    else "NA",

                "Parameters":
                    str(
                        activity["parameters"]
                    ),

                "Retry":
                    activity[
                        "retry_policy"
                    ]["retry"],

                "Timeout":
                    activity[
                        "retry_policy"
                    ]["timeout"],

                "Notebook Path":
                    activity[
                        "notebook_path"
                    ],

                "Stored Procedure":
                    activity[
                        "stored_procedure"
                    ],

                "Expressions":
                    ",".join(
                        activity[
                            "expressions"
                        ]
                    )
                    if activity[
                        "expressions"
                    ]
                    else "NA",

                "Security Issues":
                    ",".join(
                        activity[
                            "security_issues"
                        ]
                    )
                    if activity[
                        "security_issues"
                    ]
                    else "NA"
            })

        activities_df = pd.DataFrame(
            rows
        )

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

            for dataset in activity[
                "datasets"
            ]:

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
        # Retry Policies
        # -----------------------------------

        st.subheader(
            "Retry Policies"
        )

        retry_rows = []

        for activity in activities:

            retry_rows.append({

                "Activity":
                    activity["name"],

                "Retry":
                    activity[
                        "retry_policy"
                    ]["retry"],

                "Timeout":
                    activity[
                        "retry_policy"
                    ]["timeout"]
            })

        retry_df = pd.DataFrame(
            retry_rows
        )

        st.dataframe(

            retry_df,

            width="stretch"
        )

        # -----------------------------------
        # Security Issues
        # -----------------------------------

        st.subheader(
            "Security Issues"
        )

        security_rows = []

        for activity in activities:

            for issue in activity[
                "security_issues"
            ]:

                security_rows.append({

                    "Activity":
                        activity["name"],

                    "Issue":
                        issue
                })

        if security_rows:

            security_df = pd.DataFrame(
                security_rows
            )

            st.dataframe(

                security_df,

                width="stretch"
            )

        else:

            st.success(
                "No Security Issues Found"
            )

        # -----------------------------------
        # Optimization Recommendations
        # -----------------------------------

        st.subheader(
            "Optimization Recommendations"
        )

        if optimization:

            for recommendation in optimization:

                st.warning(
                    recommendation
                )

        else:

            st.success(
                "No Optimization Issues Found"
            )

        # -----------------------------------
        # Dependency Graph
        # -----------------------------------
        st.subheader(
        "Dependency Graph Color Guide"
        )

        legend_rows = [

            {

                "Color":
                    "🔵",

                "Meaning":
                    "Container / Orchestration Activities"
            },

            {

                "Color":
                    "🟢",

                "Meaning":
                    "Processing Activities"
            },

            {

                "Color":
                    "⚪",

                "Meaning":
                    "Utility / Metadata Activities"
            },

            {

                "Color":
                    "🔴",

                "Meaning":
                    "Failure Activities"
            }
        ]

        legend_df = pd.DataFrame(
            legend_rows
        )

        st.dataframe(

            legend_df,

            width="stretch",

            hide_index=True
        )

        st.subheader(
            "Dependency Graph"
        )
        dependency_graph = (
            generate_dependency_graph(
                activities
            )
        )

        st.graphviz_chart(
            dependency_graph
        )

        # -----------------------------------
        # Dataset Lineage
        # -----------------------------------

        st.subheader(
            "Dataset Lineage"
        )
        lineage_graph = (
            generate_lineage_graph(
                lineage
            )
        )

        st.graphviz_chart(
            lineage_graph
        )

        # -----------------------------------
        # Impact Analysis
        # -----------------------------------

        st.subheader(
            "Impact Analysis"
        )

        impact_df = pd.DataFrame(
            impact_analysis
        )

        st.dataframe(

            impact_df,

            width="stretch"
        )

        # -----------------------------------
        # Excel Export
        # -----------------------------------

        st.subheader(
            "Export Report"
        )

        excel_path = create_excel_report(

            pipeline_name,

            activities,

            lineage,

            optimization,

            impact_analysis
        )
        word_path = create_word_report(
        pipeline_name,
        pipeline_parameters,  # <--- Add this
        pipeline_variables,
        activities,
        lineage,
        optimization,
        impact_analysis
    )
        

        col1, col2 = st.columns(2)

        # -----------------------------------
        # EXCEL DOWNLOAD
        # -----------------------------------

        with col1:

            with open(
                excel_path,
                "rb"
            ) as file:

                st.download_button(

                    label="Download Excel Report",

                    data=file,

                    file_name=(
                        f"{pipeline_name}_enterprise_report.xlsx"
                    ),

                    key=f"excel_{pipeline_name}"
                )

        # -----------------------------------
        # WORD DOWNLOAD
        # -----------------------------------

        with col2:

            with open(
                word_path,
                "rb"
            ) as file:

                st.download_button(

                    label="Download Word Documentation",

                    data=file,

                    file_name=(
                        f"{pipeline_name}_documentation.docx"
                    ),

                    key=f"word_{pipeline_name}"
                )
        st.divider()
  