import io
from graphviz import Digraph

def get_activity_color(activity_type):
    """Returns hex color codes based on the ADF activity category."""
    orchestration = ["ForEach", "IfCondition", "Until", "ExecutePipeline"]
    processing = ["Copy", "ExecuteDataFlow", "DatabricksNotebook", "SqlServerStoredProcedure"]
    utility = ["Lookup", "GetMetadata", "SetVariable", "Wait", "WebActivity"]
    failure = ["Fail"]

    if activity_type in orchestration:
        return "#42A5F5"  # Blue
    elif activity_type in processing:
        return "#66BB6A"  # Green
    elif activity_type in utility:
        return "#BDBDBD"  # Grey
    elif activity_type in failure:
        return "#EF5350"  # Red
        
    return "#D3D3D3"  # Default Grey

def generate_dependency_graph(activities):
    """Builds a Graphviz Digraph visualizing pipeline activity dependencies."""
    dot = Digraph()
    dot.attr(rankdir="LR", splines="ortho", nodesep="0.7", ranksep="1")
    dot.attr("node", shape="box", style="rounded,filled", fontname="Helvetica")

    # Create nodes for each activity
    for activity in activities:
        label = f"{activity['name']}\n[{activity['type']}]"
        fill_color = get_activity_color(activity["type"])
        dot.node(activity["name"], label=label, fillcolor=fill_color)

    # Draw dependency edges
    for activity in activities:
        
        # Standard dependsOn relationships
        for dependency in activity.get("depends_on", []):
            source = dependency["activity"]
            conditions = ",".join(dependency.get("conditions", []))

            if "Succeeded" in conditions:
                edge_label, edge_color = "SUCCESS", "green"
            elif "Failed" in conditions:
                edge_label, edge_color = "FAILED", "red"
            elif "Completed" in conditions:
                edge_label, edge_color = "COMPLETED", "blue"
            else:
                edge_label, edge_color = conditions, "black"

            dot.edge(source, activity["name"], color=edge_color, label=edge_label, penwidth="2")

        # Parent container relationships (e.g., inside a ForEach or Switch)
        if activity.get("parent"):
            dot.edge(activity["parent"], activity["name"], style="dashed", color="gray")

    return dot

def get_dependency_graph_image_buffer(graph):
    """
    Renders the graph to a PNG in-memory buffer for enterprise security.
    (Replaces the old local disk save logic).
    """
    png_data = graph.pipe(format='png')
    return io.BytesIO(png_data)