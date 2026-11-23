import networkx as nx


def build_association_network(rules_df):
    graph = nx.DiGraph()

    if rules_df is None or rules_df.empty:
        return graph

    for _, row in rules_df.iterrows():

        antecedents = list(row["antecedents"])
        consequents = list(row["consequents"])

        for product_a in antecedents:
            for product_b in consequents:

                graph.add_edge(
                    product_a,
                    product_b,
                    confidence=float(row["confidence"]),
                    lift=float(row["lift"]),
                    support=float(row["support"])
                )

    return graph


def get_network_data(graph):
    nodes = [
        {"id": node, "label": str(node)}
        for node in graph.nodes()
    ]

    edges = [
        {
            "source": source,
            "target": target,
            "lift": data.get("lift", 0),
            "confidence": data.get("confidence", 0)
        }
        for source, target, data in graph.edges(data=True)
    ]

    return {
        "nodes": nodes,
        "edges": edges
    }