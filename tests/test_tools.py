import pytest

from bioagentx.tools.registry import build_default_registry


@pytest.mark.asyncio
async def test_tools_return_structured_json_and_cache() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)

    result, cached = await registry.call("gene_lookup", {"gene": "BRCA1"})
    again, cached_again = await registry.call("gene_lookup", {"gene": "BRCA1"})

    assert result.output["found"] is True
    assert result.output["name"] == "BRCA1"
    assert cached is False
    assert cached_again is True
    assert again.output == result.output


@pytest.mark.asyncio
async def test_stats_analysis_extracts_numbers() -> None:
    registry = build_default_registry(cache_ttl_seconds=60)
    result, _ = await registry.call("stats_analysis", {"query": "values 1 2 3 4"})

    assert result.output["n"] == 4
    assert result.output["mean"] == 2.5
