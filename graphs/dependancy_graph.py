from graphviz import Digraph


def get_activity_color(
    activity_type
):

    orchestration = [

        "ForEach",
        "IfCondition",
        "Until",
        "ExecutePipeline"
    ]

    processing = [

        "Copy",
        "ExecuteDataFlow",
        "DatabricksNotebook",
        "SqlServerStoredProcedure"
    ]

    utility = [

        "Lookup",
        "GetMetadata",
        "SetVariable",
        "Wait",
        "WebActivity"
    ]

    failure = [

        "Fail"
    ]

    if activity_type in orchestration:

        return "#42A5F5"

    elif activity_type in processing:

        return "#66BB6A"

    elif activity_type in utility:

        return "#BDBDBD"

    elif activity_type in failure:

        return "#EF5350"

    return "#D3D3D3"


def generate_dependency_graph(
    activities
):

    dot = Digraph()

    dot.attr(

        rankdir="LR",

        splines="ortho",

        nodesep="0.7",

        ranksep="1"
    )

    dot.attr(

        "node",

        shape="box",

        style="rounded,filled",

        fontname="Helvetica"
    )

    # -----------------------------------
    # Create Nodes
    # -----------------------------------

    for activity in activities:

        label = (
            f"{activity['name']}\n"
            f"[{activity['type']}]"
        )

        fill_color = get_activity_color(
            activity["type"]
        )

        dot.node(

            activity["name"],

            label=label,

            fillcolor=fill_color
        )

    # -----------------------------------
    # Dependency Edges
    # -----------------------------------

    for activity in activities:

        # dependsOn edges
        for dependency in activity[
            "depends_on"
        ]:

            source = dependency[
                "activity"
            ]

            conditions = ",".join(
                dependency["conditions"]
            )

            if "Succeeded" in conditions:

                edge_label = "SUCCESS"

            elif "Failed" in conditions:

                edge_label = "FAILED"

            elif "Completed" in conditions:

                edge_label = "COMPLETED"

            else:

                edge_label = conditions

            edge_color = "black"

            if "Failed" in conditions:

                edge_color = "red"

            elif "Succeeded" in conditions:

                edge_color = "green"

            elif "Completed" in conditions:

                edge_color = "blue"

            dot.edge(

                source,

                activity["name"],

                color=edge_color,

                label=edge_label,

                penwidth="2"
            )

        # -----------------------------------
        # Parent Container Relationship
        # -----------------------------------

        if activity["parent"]:

            dot.edge(

                activity["parent"],

                activity["name"],

                style="dashed",

                color="gray"
            )

    return dot

# -----------------------------------
# SAVE GRAPH IMAGE
# -----------------------------------

def save_dependency_graph_image(

    graph,

    pipeline_name
):

    import os

    os.makedirs(

        "docs/graphs",

        exist_ok=True
    )

    safe_name = (

        pipeline_name
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    output_path = (

        f"docs/graphs/"
        f"{safe_name}_dependency"
    )

    graph.render(

        output_path,

        format="png",

        cleanup=True
    )

    return f"{output_path}.png"