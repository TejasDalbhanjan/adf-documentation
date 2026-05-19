def build_impact_analysis(
    activities
):

    impact = []

    for activity in activities:

        for dataset in activity.get(
            "datasets",
            []
        ):

            impact.append({

                "dataset":
                    dataset,

                "activity":
                    activity["name"]
            })

    return impact