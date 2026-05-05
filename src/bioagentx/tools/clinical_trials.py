from bioagentx.tools.base import BioTool

TRIALS: list[dict[str, str]] = [
    {"trial_id": "NCT-BRCA-001", "gene": "BRCA1", "disease": "breast cancer", "phase": "Phase 2", "status": "Recruiting", "intervention": "PARP inhibitor combination"},
    {"trial_id": "NCT-EGFR-101", "gene": "EGFR", "disease": "lung cancer", "phase": "Phase 3", "status": "Active, not recruiting", "intervention": "EGFR tyrosine kinase inhibitor"},
    {"trial_id": "NCT-TNF-201", "gene": "TNF", "disease": "rheumatoid arthritis", "phase": "Phase 4", "status": "Completed", "intervention": "TNF inhibitor safety monitoring"},
    {"trial_id": "NCT-APOE-301", "gene": "APOE", "disease": "Alzheimer disease", "phase": "Observational", "status": "Recruiting", "intervention": "Genotype-informed risk cohort"},
]


class ClinicalTrialSearchTool(BioTool):
    """Search mock clinical trial metadata by gene and disease."""

    name = "clinical_trial_search"
    description = "Search mock clinical trial metadata by gene and disease."

    async def run(self, tool_input: dict[str, object]) -> dict[str, object]:
        gene = str(tool_input.get("gene", "")).upper() if tool_input.get("gene") else None
        disease = str(tool_input.get("disease", "")).lower() if tool_input.get("disease") else None
        matches = []
        for trial in TRIALS:
            if gene and trial["gene"].upper() != gene:
                continue
            if disease and disease not in trial["disease"].lower():
                continue
            matches.append(trial)
        return {
            "query": {"gene": gene, "disease": disease},
            "trials": matches,
            "count": len(matches),
            "evidence": [trial["trial_id"] for trial in matches],
        }
