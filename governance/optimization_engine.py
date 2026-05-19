def generate_optimization_recommendations(
    activities
):

    recommendations = []

    copy_count = sum(

        1

        for activity in activities

        if activity["type"] == "Copy"
    )

    if copy_count > 10:

        recommendations.append(
            "Consider parallel copy optimization"
        )

    notebook_count = sum(

        1

        for activity in activities

        if "Notebook" in activity["type"]
    )

    if notebook_count > 5:

        recommendations.append(
            "Large notebook chain detected"
        )

    foreach_count = sum(

        1

        for activity in activities

        if activity["type"] == "ForEach"
    )

    if foreach_count > 3:

        recommendations.append(
            "Multiple ForEach loops detected"
        )

    return recommendations