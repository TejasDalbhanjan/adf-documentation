import io
from docx import Document
from docx.shared import Pt

def build_dependency_flow(activities):
    flow_text = ""
    for activity in activities:
        activity_name = activity["name"]
        activity_type = activity["type"]
        depends_on = activity["depends_on"]
        parent = activity["parent"]

        flow_text += f"\n\nActivity: {activity_name}\nType: {activity_type}\n"

        if parent:
            flow_text += f"Parent Container: {parent}\n"

        if depends_on:
            flow_text += "Depends On:\n"
            for dep in depends_on:
                dependency_name = dep.get("activity", "NA")
                
                # Use "conditions", which is the key set by the parser
                conditions = dep.get("conditions", [])
                if conditions:
                    cond_str = ",".join(conditions)
                    flow_text += f"   -> {dependency_name} ({cond_str})\n"
                else:
                    flow_text += f"   -> {dependency_name}\n"
        else:
            flow_text += "Depends On: ROOT ACTIVITY\n"

    return flow_text

def build_lineage_flow(lineage):
    lineage_text = ""
    for item in lineage:
        source = item.get("source", "NA")
        activity = item.get("activity", "NA")
        target = item.get("target", "NA")

        lineage_text += (
            f"{source}"
            f"\n   ↓\n"
            f"{activity}"
            f"\n   ↓\n"
            f"{target}"
            f"\n\n"
        )
    return lineage_text


def create_word_report(
    pipeline_name,
    pipeline_parameters,  
    pipeline_variables,   
    activities,
    lineage,
    optimization,
    impact_analysis
):
    document = Document()

    title = document.add_heading(f"ADF Enterprise Documentation - {pipeline_name}", level=1)
    title.runs[0].font.size = Pt(24)

    document.add_heading("Executive Summary", level=2)
    document.add_paragraph(
f"""Pipeline Name: {pipeline_name}

Pipeline Parameters: {pipeline_parameters if pipeline_parameters else 'None'}
Pipeline Variables: {pipeline_variables if pipeline_variables else 'None'}

Total Activities: {len(activities)}

This document contains enterprise-level
ADF pipeline analysis including:

• Activity orchestration
• Dependency analysis
• Dataset lineage
• Optimization findings
• Impact analysis
• Governance review
"""
    )

 
    document.add_heading("Pipeline Execution Flow", level=2)
    dependency_flow = build_dependency_flow(activities)
    paragraph = document.add_paragraph()
    run = paragraph.add_run(dependency_flow)
    run.font.name = "Courier New"
    run.font.size = Pt(9)

    document.add_heading("Dataset Lineage Flow", level=2)
    lineage_flow = build_lineage_flow(lineage)
    paragraph = document.add_paragraph()
    run = paragraph.add_run(lineage_flow)
    run.font.name = "Courier New"
    run.font.size = Pt(9)

    document.add_heading("Activity Details", level=1)

    for activity in activities:
        document.add_heading(activity["name"], level=2)
        table = document.add_table(rows=0, cols=2)
        table.style = "Table Grid"

        fields = [
            ("Type", activity["type"]),
            ("Parent", activity["parent"] if activity["parent"] else "NA"),
            ("Datasets", ",".join(activity["datasets"]) if activity["datasets"] else "NA"),
            ("Linked Services", ",".join(activity["linked_services"]) if activity["linked_services"] else "NA"),
            ("Pipelines", ",".join(activity["pipelines"]) if activity["pipelines"] else "NA"),
            ("Dataflows", ",".join(activity["dataflows"]) if activity["dataflows"] else "NA"),
            ("Notebook Path", activity["notebook_path"]),
            ("Stored Procedure", activity["stored_procedure"]),
            ("Expressions", "\n".join(activity["expressions"]) if activity["expressions"] else "NA"),
            ("Parameters", str(activity.get("parameters", {}))),  
            ("Retry", str(activity["retry_policy"].get("retry", 0))),
            ("Timeout", str(activity["retry_policy"].get("timeout", "NA")))
        ]

        for key, value in fields:
            row_cells = table.add_row().cells
            row_cells[0].text = str(key)
            row_cells[1].text = str(value)

        document.add_paragraph("")


    document.add_heading("Impact Analysis", level=2)
    if impact_analysis:
        for impact in impact_analysis:
            document.add_paragraph(str(impact), style="List Bullet")
    else:
        document.add_paragraph("No impact issues found.")


    document.add_heading("Optimization Recommendations", level=2)
    if optimization:
        for recommendation in optimization:
            document.add_paragraph(recommendation, style="List Bullet")
    else:
        document.add_paragraph("No optimization findings.")

    # NEW: Save to a byte stream instead of a file on disk
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    
    return buffer