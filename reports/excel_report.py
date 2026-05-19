import os
import pandas as pd

from utils.helpers import (
    safe_join,
    safe_dict
)


def create_excel_report(

    pipeline_name,

    activities,

    lineage,

    optimization,

    impact_analysis
):

    os.makedirs(

        "docs/excel",

        exist_ok=True
    )

    output_path = (

        f"docs/excel/"
        f"{safe_pipeline_name}_enterprise_report.xlsx"
    )

    with pd.ExcelWriter(

        output_path,

        engine="xlsxwriter"
    ) as writer:

        # -----------------------------------
        # Summary
        # -----------------------------------

        summary_df = pd.DataFrame([{

            "Pipeline Name":
                pipeline_name,

            "Total Activities":
                len(activities),

            "Dependencies":
                sum(
                    len(a["depends_on"])
                    for a in activities
                ),

            "Datasets":
                len(set(

                    dataset

                    for activity in activities

                    for dataset in activity[
                        "datasets"
                    ]
                ))
        }])

        summary_df.to_excel(

            writer,

            sheet_name="Summary",

            index=False
        )

        # -----------------------------------
        # Activities
        # -----------------------------------

        activity_rows = []

        for activity in activities:

            activity_rows.append({

                "Activity":
                    activity["name"],

                "Type":
                    activity["type"],

                "Parent":
                    activity["parent"]
                    if activity["parent"]
                    else "NA",

                "Depends On":
                    safe_join([
                        dep["activity"]
                        for dep in activity[
                            "depends_on"
                        ]
                    ]),

                "Datasets":
                    safe_join(
                        activity["datasets"]
                    ),

                "Linked Services":
                    safe_join(
                        activity[
                            "linked_services"
                        ]
                    ),

                "Dataflows":
                    safe_join(
                        activity[
                            "dataflows"
                        ]
                    ),

                "Pipelines":
                    safe_join(
                        activity[
                            "pipelines"
                        ]
                    ),

                "Parameters":
                    safe_dict(
                        activity[
                            "parameters"
                        ]
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
                    safe_join(
                        activity[
                            "expressions"
                        ]
                    ),

                "Security Issues":
                    safe_join(
                        activity[
                            "security_issues"
                        ]
                    )
            })

        activities_df = pd.DataFrame(
            activity_rows
        )

        activities_df.to_excel(

            writer,

            sheet_name="Activities",

            index=False
        )

        # -----------------------------------
        # Lineage
        # -----------------------------------

        lineage_df = pd.DataFrame(
            lineage
        )

        lineage_df.to_excel(

            writer,

            sheet_name="Lineage",

            index=False
        )

        # -----------------------------------
        # Impact Analysis
        # -----------------------------------

        impact_df = pd.DataFrame(
            impact_analysis
        )

        impact_df.to_excel(

            writer,

            sheet_name="ImpactAnalysis",

            index=False
        )

        # -----------------------------------
        # Optimization
        # -----------------------------------

        optimization_df = pd.DataFrame({

            "Recommendations":
                optimization
        })

        optimization_df.to_excel(

            writer,

            sheet_name="Optimization",

            index=False
        )

    return output_path