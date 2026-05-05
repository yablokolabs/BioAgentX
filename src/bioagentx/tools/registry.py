import json
from typing import Any

from bioagentx.core.cache import AsyncTTLCache
from bioagentx.core.metrics import TOOL_CALLS
from bioagentx.tools.base import BioTool, ToolResult
from bioagentx.tools.clinical_trials import ClinicalTrialSearchTool
from bioagentx.tools.gene_lookup import GeneLookupTool
from bioagentx.tools.pathway_analysis import PathwayAnalysisTool
from bioagentx.tools.stats_analysis import StatsAnalysisTool


class ToolRegistry:
    """Central registry for bio-tools with optional result caching."""

    def __init__(self, tools: list[BioTool], cache: AsyncTTLCache[ToolResult] | None = None) -> None:
        self.tools = {tool.name: tool for tool in tools}
        self.cache = cache

    async def call(self, name: str, tool_input: dict[str, Any]) -> tuple[ToolResult, bool]:
        """Invoke a tool by name, returning ``(result, was_cached)``."""
        if name not in self.tools:
            TOOL_CALLS.labels(tool=name, status="missing").inc()
            raise KeyError(f"Unknown tool: {name}")
        cache_key = (name, json.dumps(tool_input, sort_keys=True, default=str))
        if self.cache is not None:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                TOOL_CALLS.labels(tool=name, status="cached").inc()
                return cached, True
        result = await self.tools[name](tool_input)
        if self.cache is not None:
            await self.cache.set(cache_key, result)
        TOOL_CALLS.labels(tool=name, status="ok").inc()
        return result, False


def build_default_registry(cache_ttl_seconds: int = 300, *, max_cache_size: int = 2048) -> ToolRegistry:
    """Construct a :class:`ToolRegistry` with all built-in bio-tools."""
    return ToolRegistry(
        tools=[GeneLookupTool(), PathwayAnalysisTool(), ClinicalTrialSearchTool(), StatsAnalysisTool()],
        cache=AsyncTTLCache[ToolResult](cache_ttl_seconds, max_size=max_cache_size),
    )
