from bioagentx.tools.base import BioTool

GENE_DB: dict[str, dict[str, object]] = {
    "BRCA1": {
        "name": "BRCA1",
        "full_name": "BRCA1 DNA repair associated",
        "chromosome": "17q21.31",
        "function": "Tumor suppressor involved in homologous recombination DNA repair.",
        "clinical_relevance": "Pathogenic variants increase hereditary breast and ovarian cancer risk.",
        "evidence": ["HGNC:1100", "PMID:1001"],
    },
    "TP53": {
        "name": "TP53",
        "full_name": "tumor protein p53",
        "chromosome": "17p13.1",
        "function": "Regulates DNA-damage response, apoptosis, and cell-cycle arrest.",
        "clinical_relevance": "Frequently altered tumor suppressor across cancer types.",
        "evidence": ["HGNC:11998", "PMID:1002"],
    },
    "EGFR": {
        "name": "EGFR",
        "full_name": "epidermal growth factor receptor",
        "chromosome": "7p11.2",
        "function": "Receptor tyrosine kinase activating proliferative signaling.",
        "clinical_relevance": "Activating mutations guide targeted therapy in NSCLC.",
        "evidence": ["HGNC:3236", "PMID:1003"],
    },
    "APOE": {
        "name": "APOE",
        "full_name": "apolipoprotein E",
        "chromosome": "19q13.32",
        "function": "Lipid transport and neuronal maintenance.",
        "clinical_relevance": "APOE epsilon4 is associated with Alzheimer disease risk.",
        "evidence": ["HGNC:613", "PMID:1004"],
    },
    "TNF": {
        "name": "TNF",
        "full_name": "tumor necrosis factor",
        "chromosome": "6p21.33",
        "function": "Inflammatory cytokine regulating immune responses.",
        "clinical_relevance": "Therapeutic inhibition is used in autoimmune inflammatory disease.",
        "evidence": ["HGNC:11892", "PMID:1005"],
    },
}


class GeneLookupTool(BioTool):
    """Return structured gene annotation and clinical relevance from a local demo database."""

    name = "gene_lookup"
    description = "Return structured gene annotation and clinical relevance."

    async def run(self, tool_input: dict[str, object]) -> dict[str, object]:
        gene = str(tool_input.get("gene", "")).upper()
        record = GENE_DB.get(gene)
        if record is None:
            return {"found": False, "gene": gene, "evidence": [], "message": "No local gene record found."}
        return {"found": True, **record}
