from bioagentx.knowledge_graph.graph import KnowledgeGraph
from bioagentx.knowledge_graph.seed import build_seed_graph


def test_graph_expands_neighbors_and_relationships() -> None:
    graph = build_seed_graph()
    neighborhood = graph.neighborhood("BRCA1", depth=2)

    assert "BRCA1" in neighborhood.expanded_terms
    assert any(edge.relationship == "interacts_with" for edge in neighborhood.edges)
    assert any(edge.relationship == "causes" for edge in neighborhood.edges)
    assert any(node.node_type == "disease" for node in neighborhood.nodes)


def test_extract_known_terms() -> None:
    graph = build_seed_graph()
    terms = graph.extract_known_terms("BRCA1 and breast cancer pathway analysis")

    assert "BRCA1" in terms["genes"]
    assert "breast cancer" in terms["diseases"]


def test_resolve_by_alias() -> None:
    graph = build_seed_graph()
    node = graph.resolve("NSCLC")

    assert node is not None
    assert node.name == "lung cancer"


def test_resolve_unknown_term() -> None:
    graph = build_seed_graph()
    assert graph.resolve("nonexistent_entity") is None


def test_neighborhood_unknown_seed() -> None:
    graph = build_seed_graph()
    nb = graph.neighborhood("nonexistent_entity")

    assert nb.nodes == []
    assert nb.edges == []
    assert nb.expanded_terms == []


def test_empty_graph() -> None:
    graph = KnowledgeGraph(nodes=[], edges=[])
    assert graph.resolve("anything") is None
    assert graph.extract_known_terms("anything") == {"genes": [], "diseases": [], "pathways": []}
