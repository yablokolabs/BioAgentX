from bioagentx.knowledge_graph.graph import GraphEdge, GraphNode, KnowledgeGraph


def build_seed_graph() -> KnowledgeGraph:
    """Construct the demo knowledge graph with 15 biomedical nodes and 13 edges."""
    nodes = [
        GraphNode(
            node_id="gene:BRCA1", node_type="gene", name="BRCA1", aliases=["breast cancer gene 1"]
        ),
        GraphNode(node_id="gene:TP53", node_type="gene", name="TP53", aliases=["p53"]),
        GraphNode(node_id="gene:EGFR", node_type="gene", name="EGFR", aliases=["ERBB1"]),
        GraphNode(node_id="gene:APOE", node_type="gene", name="APOE", aliases=["apolipoprotein E"]),
        GraphNode(node_id="gene:TNF", node_type="gene", name="TNF", aliases=["TNF-alpha"]),
        GraphNode(node_id="disease:breast_cancer", node_type="disease", name="breast cancer"),
        GraphNode(node_id="disease:ovarian_cancer", node_type="disease", name="ovarian cancer"),
        GraphNode(
            node_id="disease:lung_cancer",
            node_type="disease",
            name="lung cancer",
            aliases=["NSCLC"],
        ),
        GraphNode(
            node_id="disease:alzheimer",
            node_type="disease",
            name="Alzheimer disease",
            aliases=["Alzheimer's disease"],
        ),
        GraphNode(
            node_id="disease:rheumatoid_arthritis", node_type="disease", name="rheumatoid arthritis"
        ),
        GraphNode(node_id="pathway:dna_repair", node_type="pathway", name="DNA repair"),
        GraphNode(node_id="pathway:p53", node_type="pathway", name="p53 signaling"),
        GraphNode(node_id="pathway:egfr", node_type="pathway", name="EGFR signaling"),
        GraphNode(
            node_id="pathway:inflammation", node_type="pathway", name="inflammatory signaling"
        ),
        GraphNode(node_id="pathway:lipid", node_type="pathway", name="lipid transport"),
    ]
    edges = [
        GraphEdge(
            source="gene:BRCA1",
            target="gene:TP53",
            relationship="interacts_with",
            evidence="DNA damage response crosstalk",
        ),
        GraphEdge(
            source="gene:BRCA1",
            target="disease:breast_cancer",
            relationship="causes",
            evidence="pathogenic variants elevate inherited risk",
        ),
        GraphEdge(
            source="gene:BRCA1",
            target="disease:ovarian_cancer",
            relationship="causes",
            evidence="pathogenic variants elevate inherited risk",
        ),
        GraphEdge(
            source="gene:BRCA1",
            target="pathway:dna_repair",
            relationship="interacts_with",
            evidence="homologous recombination repair",
        ),
        GraphEdge(
            source="gene:TP53",
            target="pathway:p53",
            relationship="interacts_with",
            evidence="canonical tumor-suppressor pathway",
        ),
        GraphEdge(
            source="gene:TP53",
            target="pathway:egfr",
            relationship="inhibits",
            evidence="p53 can suppress proliferative signaling",
        ),
        GraphEdge(
            source="gene:EGFR",
            target="disease:lung_cancer",
            relationship="causes",
            evidence="activating mutations drive NSCLC subsets",
        ),
        GraphEdge(
            source="gene:EGFR",
            target="pathway:egfr",
            relationship="interacts_with",
            evidence="receptor tyrosine kinase signaling",
        ),
        GraphEdge(
            source="gene:APOE",
            target="disease:alzheimer",
            relationship="causes",
            evidence="epsilon4 allele increases population risk",
        ),
        GraphEdge(
            source="gene:APOE",
            target="pathway:lipid",
            relationship="interacts_with",
            evidence="lipoprotein transport",
        ),
        GraphEdge(
            source="gene:TNF",
            target="disease:rheumatoid_arthritis",
            relationship="causes",
            evidence="pro-inflammatory cytokine activity",
        ),
        GraphEdge(
            source="gene:TNF",
            target="pathway:inflammation",
            relationship="interacts_with",
            evidence="cytokine cascade",
        ),
        GraphEdge(
            source="pathway:inflammation",
            target="pathway:dna_repair",
            relationship="inhibits",
            evidence="chronic inflammation can increase DNA damage burden",
        ),
    ]
    return KnowledgeGraph(nodes=nodes, edges=edges)
