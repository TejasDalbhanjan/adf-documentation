from graphviz import Digraph


def generate_lineage_graph(
    lineage
):

    dot = Digraph()

    dot.attr(rankdir="LR")

    for item in lineage:

        dot.edge(

            item["source"],

            item["target"],

            label=item["activity"]
        )

    return dot


# -----------------------------------
# SAVE LINEAGE GRAPH IMAGE
# -----------------------------------

def save_lineage_graph_image(

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
        f"{safe_name}_lineage"
    )

    source = source(graph)

    source.render(

        output_path,

        format="png",

        cleanup=True
    )

    return f"{output_path}.png"