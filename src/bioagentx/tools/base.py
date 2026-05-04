import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool_name: str
    input: dict[str, Any]
    output: dict[str, Any]
    evidence: list[str] = Field(default_factory=list)
    latency_ms: float


class BioTool(ABC):
    name: str
    description: str

    async def __call__(self, tool_input: dict[str, Any]) -> ToolResult:
        start = time.perf_counter()
        output = await self.run(tool_input)
        return ToolResult(
            tool_name=self.name,
            input=tool_input,
            output=output,
            evidence=output.get("evidence", []) if isinstance(output, dict) else [],
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    @abstractmethod
    async def run(self, tool_input: dict[str, Any]) -> dict[str, Any]: ...
