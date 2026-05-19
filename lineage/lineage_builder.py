def build_dataset_lineage(
    activities
):

    lineage = []

    for activity in activities:

        datasets = activity.get(
            "datasets",
            []
        )

        if len(datasets) >= 2:

            lineage.append({

                "source":
                    datasets[0],

                "target":
                    datasets[-1],

                "activity":
                    activity["name"]
            })

    return lineage