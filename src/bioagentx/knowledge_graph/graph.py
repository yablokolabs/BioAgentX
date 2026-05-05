from collections import defaultdict, deque

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """A single entity (gene, disease, pathway) in the knowledge graph."""

    node_id: str
    node_type: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    properties: dict[str, str] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed relationship between two graph nodes."""

    source: str
    target: str
    relationship: str
    evidence: str | None = None


class GraphNeighborhood(BaseModel):
    """BFS expansion result from a seed term."""

    seed: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    expanded_terms: list[str]


class KnowledgeGraph:
    """In-memory biomedical knowledge graph with deterministic BFS expansion.

    Nodes are genes, diseases, and pathways.  Edges represent causal,
    inhibitory, and interaction relationships.  Reverse edges are created
    automatically so traversal works in both directions.
    """

    def __init__(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        self.nodes = {node.node_id: node for node in nodes}
        self.name_index: dict[str, str] = {}
        for node in nodes:
            self.name_index[node.name.lower()] = node.node_id
            for alias in node.aliases:
                self.name_index[alias.lower()] = node.node_id
        self.edges = edges
        self.adjacency: dict[str, list[GraphEdge]] = defaultdict(list)
        for edge in edges:
            self.adjacency[edge.source].append(edge)
            self.adjacency[edge.target].append(
                GraphEdge(
                    source=edge.target,
                    target=edge.source,
                    relationship=f"inverse_{edge.relationship}",
                    evidence=edge.evidence,
                )
            )

    def resolve(self, term: str) -> GraphNode | None:
        """Look up a node by name or alias (case-insensitive)."""
        node_id = self.name_index.get(term.lower())
        return self.nodes.get(node_id) if node_id else None

    def extract_known_terms(self, query: str) -> dict[str, list[str]]:
        """Return genes, diseases, and pathways mentioned in *query*."""
        lowered = query.lower()
        genes: list[str] = []
        diseases: list[str] = []
        pathways: list[str] = []
        for node in self.nodes.values():
            terms = [node.name, *node.aliases]
            if any(term.lower() in lowered for term in terms):
                if node.node_type == "gene":
                    genes.append(node.name)
                elif node.node_type == "disease":
                    diseases.append(node.name)
                elif node.node_type == "pathway":
                    pathways.append(node.name)
        return {
            "genes": sorted(set(genes)),
            "diseases": sorted(set(diseases)),
            "pathways": sorted(set(pathways)),
        }

    def neighborhood(self, seed: str, depth: int = 2) -> GraphNeighborhood:
        """Return all nodes and edges reachable from *seed* within *depth* hops."""
        start = self.resolve(seed)
        if start is None:
            return GraphNeighborhood(seed=seed, nodes=[], edges=[], expanded_terms=[])
        visited_nodes = {start.node_id}
        visited_edges: list[GraphEdge] = []
        queue: deque[tuple[str, int]] = deque([(start.node_id, 0)])
        while queue:
            node_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            for edge in self.adjacency.get(node_id, []):
                visited_edges.append(edge)
                if edge.target not in visited_nodes:
                    visited_nodes.add(edge.target)
                    queue.append((edge.target, current_depth + 1))
        nodes = [self.nodes[node_id] for node_id in visited_nodes]
        expanded = sorted({term for node in nodes for term in [node.name, *node.aliases]})
        return GraphNeighborhood(seed=start.name, nodes=nodes, edges=visited_edges, expanded_terms=expanded)

    def expand_terms(self, seeds: list[str], depth: int = 2) -> dict[str, GraphNeighborhood]:
        """Expand multiple seed terms into their graph neighborhoods."""
        return {seed: self.neighborhood(seed, depth=depth) for seed in seeds}
