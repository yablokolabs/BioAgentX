from bioagentx.tools.base import BioTool

PATHWAYS = {
    "BRCA1": [
        {"pathway": "DNA repair", "enrichment_score": 0.91, "interpretation": "homologous recombination defect signal"},
        {"pathway": "p53 signaling", "enrichment_score": 0.62, "interpretation": "DNA damage checkpoint crosstalk"},
    ],
    "TP53": [
        {"pathway": "p53 signaling", "enrichment_score": 0.95, "interpretation": "cell-cycle/apoptosis regulation"},
        {"pathway": "DNA repair", "enrichment_score": 0.52, "interpretation": "damage-response coordination"},
    ],
    "EGFR": [
        {"pathway": "EGFR signaling", "enrichment_score": 0.93, "interpretation": "receptor tyrosine kinase activation"},
        {"pathway": "MAPK signaling", "enrichment_score": 0.74, "interpretation": "downstream proliferative signaling"},
    ],
    "APOE": [
        {"pathway": "lipid transport", "enrichment_score": 0.88, "interpretation": "lipoprotein trafficking"},
        {"pathway": "neuroinflammation", "enrichment_score": 0.49, "interpretation": "context-dependent risk modulation"},
    ],
    "TNF": [
        {"pathway": "inflammatory signaling", "enrichment_score": 0.96, "interpretation": "cytokine cascade activation"},
        {"pathway": "NF-kB signaling", "enrichment_score": 0.81, "interpretation": "immune transcriptional response"},
    ],
}


class PathwayAnalysisTool(BioTool):
    name = "pathway_analysis"
    description = "Return mock but structured pathway insights for genes or gene sets."

    async def run(self, tool_input: dict[str, object]) -> dict[str, object]:
        genes = tool_input.get("genes") or tool_input.get("gene") or []
        if isinstance(genes, str):
            genes = [genes]
        normalized = [str(gene).upper() for gene in genes]
        pathways = []
        for gene in normalized:
            for result in PATHWAYS.get(gene, []):
                pathways.append({"gene": gene, **result})
        pathways.sort(key=lambda item: item["enrichment_score"], reverse=True)
        return {
            "genes": normalized,
            "top_pathways": pathways[:5],
            "method": "deterministic enrichment over curated demo pathway map",
            "evidence": [f"PATHWAY:{item['pathway']}" for item in pathways[:5]],
        }
