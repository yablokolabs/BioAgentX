from bioagentx.rag.types import BioPaper

SEED_PAPERS: list[BioPaper] = [
    BioPaper(
        paper_id="pmid-1001",
        title="BRCA1 DNA repair defects and hereditary breast ovarian cancer risk",
        abstract=(
            "BRCA1 participates in homologous recombination DNA repair. Pathogenic BRCA1 "
            "variants increase hereditary breast and ovarian cancer risk and influence sensitivity "
            "to PARP inhibition in selected clinical contexts."
        ),
        source_url="https://pubmed.ncbi.nlm.nih.gov/1001/",
        year=2020,
        gene="BRCA1",
        disease="breast cancer",
        metadata={"journal": "Mock Nature Genetics"},
    ),
    BioPaper(
        paper_id="pmid-1002",
        title="TP53 pathway disruption in solid tumors",
        abstract=(
            "TP53 encodes p53, a tumor suppressor regulating DNA damage response, apoptosis, "
            "and cell-cycle arrest. Loss of p53 signaling is frequent across solid tumors."
        ),
        source_url="https://pubmed.ncbi.nlm.nih.gov/1002/",
        year=2019,
        gene="TP53",
        disease="solid tumor",
        metadata={"journal": "Mock Cancer Cell"},
    ),
    BioPaper(
        paper_id="pmid-1003",
        title="EGFR mutations and targeted therapy in non-small cell lung cancer",
        abstract=(
            "Activating EGFR mutations can drive non-small cell lung cancer. EGFR tyrosine kinase "
            "inhibitors improve outcomes for biomarker-selected patients, while resistance mechanisms "
            "require longitudinal molecular monitoring."
        ),
        source_url="https://pubmed.ncbi.nlm.nih.gov/1003/",
        year=2021,
        gene="EGFR",
        disease="lung cancer",
        metadata={"journal": "Mock JCO"},
    ),
    BioPaper(
        paper_id="pmid-1004",
        title="APOE genotype and Alzheimer disease risk stratification",
        abstract=(
            "APOE epsilon4 is associated with increased Alzheimer disease risk at a population level. "
            "Clinical interpretation requires ancestry, age, family history, and non-genetic factors."
        ),
        source_url="https://pubmed.ncbi.nlm.nih.gov/1004/",
        year=2022,
        gene="APOE",
        disease="Alzheimer disease",
        metadata={"journal": "Mock Lancet Neurology"},
    ),
    BioPaper(
        paper_id="pmid-1005",
        title="TNF inhibition and inflammatory pathway modulation",
        abstract=(
            "TNF is a central inflammatory cytokine. TNF inhibitors reduce inflammatory signaling "
            "in rheumatoid arthritis and inflammatory bowel disease, but infection risk must be evaluated."
        ),
        source_url="https://pubmed.ncbi.nlm.nih.gov/1005/",
        year=2018,
        gene="TNF",
        disease="rheumatoid arthritis",
        metadata={"journal": "Mock Annals Rheum Dis"},
    ),
]
