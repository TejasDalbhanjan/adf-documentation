from graphviz import Digraph


def generate_dependency_graph(activities):

    dot = Digraph()

    dot.attr(rankdir='LR')

    # -----------------------------------
    # Create Nodes
    # -----------------------------------

    for activity in activities:

        label = (
            f"{activity['name']}\n"
            f"({activity['type']})"
        )

        # datasets
        if activity["datasets"]:

            datasets = "\n".join(
                activity["datasets"]
            )

            label += (
                f"\n\nDatasets:\n"
                f"{datasets}"
            )

        dot.node(
            activity["name"],
            label
        )

    # -----------------------------------
    # Parent-child hierarchy
    # -----------------------------------

    for activity in activities:

        parent = activity["parent"]

        if parent:

            dot.edge(
                parent,
                activity["name"],
                color="blue"
            )

    # -----------------------------------
    # dependsOn relationships
    # -----------------------------------

    for activity in activities:

        for dependency in activity["depends_on"]:

            source = dependency["activity"]

            conditions = ",".join(
                dependency["conditions"]
            )

            dot.edge(
                source,
                activity["name"],
                label=conditions,
                color="red"
            )

    return dot