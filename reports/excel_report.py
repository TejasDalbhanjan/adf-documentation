import pandas as pd
import os


def create_excel_report(
    activities,
    pipeline_name
):

    os.makedirs(
        "exports",
        exist_ok=True
    )

    rows = []

    for activity in activities:

        depends_on = []

        for dep in activity["depends_on"]:

            depends_on.append(
                dep["activity"]
            )

        rows.append({

            "Activity Name": activity["name"],

            "Activity Type": activity["type"],

            "Parent Activity": activity["parent"],

            "Depends On": ",".join(depends_on),

            "Datasets": ",".join(
                activity["datasets"]
            ),

            "Parameters": str(
                activity["parameters"]
            )
        })

    df = pd.DataFrame(rows)

    output_path = (
        f"exports/"
        f"{pipeline_name}_report.xlsx"
    )

    df.to_excel(
        output_path,
        index=False
    )

    return output_path