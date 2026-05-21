import io
from graphviz import Digraph

def generate_lineage_graph(lineage):
    """Builds a Graphviz Digraph visualizing source-to-target dataset lineage."""
    dot = Digraph()
    dot.attr(rankdir="LR")

    for item in lineage:
        dot.edge(item["source"], item["target"], label=item["activity"])

    return dot

def get_lineage_graph_image_buffer(graph):
    """
    Renders the graph to a PNG in-memory buffer for enterprise security.
    (Replaces the old local disk save logic).
    """
    png_data = graph.pipe(format='png')
    return io.BytesIO(png_data)