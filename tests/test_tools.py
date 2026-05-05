import pytest

from bioagentx.tools.registry import build_default_registry


@pytest.mark.asyncio
async def test_gene_lookup_found_and_cached() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)

    result, cached = await registry.call("gene_lookup", {"gene": "BRCA1"})
    again, cached_again = await registry.call("gene_lookup", {"gene": "BRCA1"})

    assert result.output["found"] is True
    assert result.output["name"] == "BRCA1"
    assert cached is False
    assert cached_again is True
    assert again.output == result.output


@pytest.mark.asyncio
async def test_gene_lookup_not_found() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("gene_lookup", {"gene": "FAKE_GENE"})

    assert result.output["found"] is False
    assert result.output["gene"] == "FAKE_GENE"


@pytest.mark.asyncio
async def test_stats_analysis_extracts_numbers() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("stats_analysis", {"query": "values 1 2 3 4"})

    assert result.output["n"] == 4
    assert result.output["mean"] == 2.5


@pytest.mark.asyncio
async def test_stats_analysis_no_numbers() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("stats_analysis", {"query": "no numeric data here"})

    assert result.output["n"] == 0
    assert "recommended_test" in result.output


@pytest.mark.asyncio
async def test_pathway_analysis() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("pathway_analysis", {"genes": ["EGFR"]})

    assert result.output["genes"] == ["EGFR"]
    assert len(result.output["top_pathways"]) > 0


@pytest.mark.asyncio
async def test_pathway_analysis_unknown_gene() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("pathway_analysis", {"genes": ["UNKNOWN_GENE"]})

    assert result.output["genes"] == ["UNKNOWN_GENE"]
    assert result.output["top_pathways"] == []


@pytest.mark.asyncio
async def test_clinical_trial_search() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("clinical_trial_search", {"gene": "EGFR", "disease": "lung cancer"})

    assert result.output["count"] >= 1
    assert any(t["gene"] == "EGFR" for t in result.output["trials"])


@pytest.mark.asyncio
async def test_clinical_trial_search_no_match() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("clinical_trial_search", {"gene": "UNKNOWN", "disease": "nothing"})

    assert result.output["count"] == 0


@pytest.mark.asyncio
async def test_unknown_tool_raises() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    with pytest.raises(KeyError, match="Unknown tool"):
        await registry.call("nonexistent_tool", {})
