import json
import io
import pandas as pd
import plotly.express as px
import streamlit as st

from reports.word_report import create_word_report
from parser.pipeline_parser import (
    extract_pipeline_name,
    extract_pipeline_parameters,
    extract_pipeline_variables,
    extract_activities
)
from parser.arm_template_parser import is_arm_template, extract_pipelines_from_arm
from graphs.dependancy_graph import generate_dependency_graph
from graphs.lineage_graph import generate_lineage_graph
from reports.excel_report import create_excel_report
from lineage.lineage_builder import build_dataset_lineage
from lineage.impact_analysis import build_impact_analysis
from governance.optimization_engine import generate_optimization_recommendations

# Setup page configuration
st.set_page_config(page_title="Enterprise ADF Analyzer", layout="wide")

def apply_enterprise_ui():
    """Injects custom CSS to make the app look like an enterprise SaaS dashboard."""
    st.markdown("""
        <style>
            /* Create true Dashboard Cards for Metrics */
            div[data-testid="stMetric"] {
                background-color: #ffffff;
                border: 1px solid #e0e6ed;
                border-radius: 8px;
                padding: 15px 20px;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05);
            }
            
            /* Hide the default Streamlit hamburger menu and footer for a white-label look */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Style the download buttons to look premium */
            div.stButton > button:first-child {
                background-color: #0058b0;
                color: white;
                border-radius: 6px;
                border: none;
                padding: 10px 24px;
                box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
                transition: all 0.2s ease-in-out;
            }
            div.stButton > button:first-child:hover {
                background-color: #004080;
                transform: translateY(-1px);
            }
        </style>
    """, unsafe_allow_html=True)

# Apply UI styles immediately
apply_enterprise_ui()

st.title("ADF Pipeline Analyzer")

# Handle file uploads
uploaded_file = st.file_uploader("Upload ADF Pipeline JSON/ ARM Template JSON", type=["json"])

if uploaded_file:
    data = json.load(uploaded_file)
    pipelines = []

    # Determine if the file is a full ARM template or a standalone pipeline JSON
    if is_arm_template(data):
        st.success("ARM Template Detected")
        pipelines = extract_pipelines_from_arm(data)
    else:
        st.success("Single Pipeline JSON Detected")
        pipelines = [data]

    # Process and display metrics for each pipeline found
    for pipeline_data in pipelines:
        pipeline_name = extract_pipeline_name(pipeline_data, full_data=data)
        st.header(f"Pipeline: {pipeline_name}")

        # Display pipeline-level parameters and variables inside clean expanders
        colA, colB = st.columns(2)
        with colA:
            with st.expander("⚙️ View Pipeline Parameters", expanded=False):
                pipeline_parameters = extract_pipeline_parameters(pipeline_data)
                if pipeline_parameters:
                    st.json(pipeline_parameters)
                else:
                    st.info("No Parameters Found")

        with colB:
            with st.expander("📦 View Pipeline Variables", expanded=False):
                pipeline_variables = extract_pipeline_variables(pipeline_data)
                if pipeline_variables:
                    st.json(pipeline_variables)
                else:
                    st.info("No Variables Found")

        # Run the core extraction engines with a loading spinner for UX
        with st.spinner(f"Analyzing architecture and extracting lineage for {pipeline_name}..."):
            activities = extract_activities(pipeline_data, full_data=data)
            lineage = build_dataset_lineage(activities)
            impact_analysis = build_impact_analysis(activities)
            optimization = generate_optimization_recommendations(activities)

        # Display high-level pipeline metrics
        st.subheader("Pipeline Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Activities", len(activities))
        with col2:
            unique_types = len(set(activity["type"] for activity in activities))
            st.metric("Activity Types", unique_types)
        with col3:
            dependency_count = sum(len(activity["depends_on"]) for activity in activities)
            st.metric("Dependencies", dependency_count)
        with col4:
            dataset_count = len(set(
                dataset
                for activity in activities
                for dataset in activity["datasets"]
            ))
            st.metric("Datasets", dataset_count)

        # Build and display the detailed activities table
        st.subheader("Activities")
        rows = []
        for activity in activities:
            # Format dependency conditions if they exist
            depends_formatted = []
            for dep in activity["depends_on"]:
                conds = dep.get("conditions", [])
                if conds:
                    depends_formatted.append(f"{dep['activity']} ({', '.join(conds)})")
                else:
                    depends_formatted.append(dep['activity'])
            
            rows.append({
                "Activity Name": activity["name"],
                "Type": activity["type"],
                "Parent": activity["parent"] if activity["parent"] else "NA",
                "Depends On": ",\n".join(depends_formatted) if depends_formatted else "NA",
                "Datasets": ",".join(activity["datasets"]) if activity["datasets"] else "NA",
                "Linked Services": ",".join(activity["linked_services"]) if activity["linked_services"] else "NA",
                "Dataflows": ",".join(activity["dataflows"]) if activity["dataflows"] else "NA",
                "Pipelines": ",".join(activity["pipelines"]) if activity["pipelines"] else "NA",
                "Parameters": str(activity["parameters"]),
                "Retry": activity["retry_policy"]["retry"],
                "Timeout": activity["retry_policy"]["timeout"],
                "Notebook Path": activity["notebook_path"],
                "Stored Procedure": activity["stored_procedure"],
                "Expressions": ",".join(activity["expressions"]) if activity["expressions"] else "NA",
                "Security Issues": ",".join(activity["security_issues"]) if activity["security_issues"] else "NA"
            })

        activities_df = pd.DataFrame(rows)
        st.dataframe(activities_df, width="stretch")

        # Visualize activity types distribution
        st.subheader("Activity Distribution")
        chart = px.histogram(activities_df, x="Type")
        st.plotly_chart(chart, width="stretch")

        # Display Dataset usage
        st.subheader("Datasets")
        dataset_rows = []
        for activity in activities:
            for dataset in activity["datasets"]:
                dataset_rows.append({"Activity": activity["name"], "Dataset": dataset})

        if dataset_rows:
            st.dataframe(pd.DataFrame(dataset_rows), width="stretch")
        else:
            st.info("No Datasets Found")

        # Display Retry Policies
        st.subheader("Retry Policies")
        retry_rows = [
            {
                "Activity": activity["name"],
                "Retry": activity["retry_policy"]["retry"],
                "Timeout": activity["retry_policy"]["timeout"]
            }
            for activity in activities
        ]
        st.dataframe(pd.DataFrame(retry_rows), width="stretch")

        # Flag any identified security issues
        st.subheader("Security Issues")
        security_rows = [
            {"Activity": activity["name"], "Issue": issue}
            for activity in activities
            for issue in activity["security_issues"]
        ]
        if security_rows:
            st.dataframe(pd.DataFrame(security_rows), width="stretch")
        else:
            st.success("No Security Issues Found")

        # Show optimization recommendations
        st.subheader("Optimization Recommendations")
        if optimization:
            for recommendation in optimization:
                st.warning(recommendation)
        else:
            st.success("No Optimization Issues Found")

        # Render visual dependency graph
        st.subheader("Dependency Graph")
        with st.expander("🎨 View Color Guide", expanded=False):
            legend_df = pd.DataFrame([
                {"Color": "🔵", "Meaning": "Container / Orchestration Activities"},
                {"Color": "🟢", "Meaning": "Processing Activities"},
                {"Color": "⚪", "Meaning": "Utility / Metadata Activities"},
                {"Color": "🔴", "Meaning": "Failure Activities"}
            ])
            st.dataframe(legend_df, width="stretch", hide_index=True)

        st.graphviz_chart(generate_dependency_graph(activities))

        # Render dataset lineage graph
        st.subheader("Dataset Lineage")
        st.graphviz_chart(generate_lineage_graph(lineage))

        # Show impact analysis table
        st.subheader("Impact Analysis")
        st.dataframe(pd.DataFrame(impact_analysis), width="stretch")

        # Generate in-memory buffers for enterprise export
        st.subheader("Export Report")
        
        excel_buffer = create_excel_report(
            pipeline_name, activities, lineage, optimization, impact_analysis
        )
        word_buffer = create_word_report(
            pipeline_name, pipeline_parameters, pipeline_variables, 
            activities, lineage, optimization, impact_analysis
        )

        # Serve the generated reports directly from memory
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📊 Download Excel Report",
                data=excel_buffer,
                file_name=f"{pipeline_name}_enterprise_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{pipeline_name}"
            )
        with col2:
            st.download_button(
                label="📄 Download Word Documentation",
                data=word_buffer,
                file_name=f"{pipeline_name}_documentation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"word_{pipeline_name}"
            )
            
        st.divider()