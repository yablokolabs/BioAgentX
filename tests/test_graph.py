from bioagentx.knowledge_graph.seed import build_seed_graph


def test_graph_expands_neighbors_and_relationships() -> None:
    graph = build_seed_graph()
    neighborhood = graph.neighborhood("BRCA1", depth=2)

    assert "BRCA1" in neighborhood.expanded_terms
    assert any(edge.relationship == "interacts_with" for edge in neighborhood.edges)
    assert any(edge.relationship == "causes" for edge in neighborhood.edges)
    assert any(node.node_type == "disease" for node in neighborhood.nodes)
