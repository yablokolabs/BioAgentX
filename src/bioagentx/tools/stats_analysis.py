import math
import re
from statistics import mean, stdev

from bioagentx.tools.base import BioTool

NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


class StatsAnalysisTool(BioTool):
    """Compute summary statistics and simple effect estimates over supplied numeric data."""

    name = "stats_analysis"
    description = "Compute summary statistics and simple effect estimates over supplied numeric data."

    async def run(self, tool_input: dict[str, object]) -> dict[str, object]:
        values = tool_input.get("values")
        if values is None:
            values = [float(m) for m in NUMBER_RE.findall(str(tool_input.get("query", "")))]
        if not isinstance(values, list):
            values = []
        numeric = [float(v) for v in values if isinstance(v, int | float | str) and self._is_numeric(v)]
        if not numeric:
            return {
                "n": 0,
                "message": "No numeric observations supplied; returning design guidance only.",
                "recommended_test": "Define endpoint, groups, covariates, and sample size before inference.",
                "evidence": ["STAT:design-check"],
            }
        avg = mean(numeric)
        sd = stdev(numeric) if len(numeric) > 1 else 0.0
        se = sd / math.sqrt(len(numeric))
        ci_low = avg - 1.96 * se
        ci_high = avg + 1.96 * se
        return {
            "n": len(numeric),
            "mean": round(avg, 4),
            "std_dev": round(sd, 4),
            "ci95": [round(ci_low, 4), round(ci_high, 4)],
            "method": "descriptive summary with normal-approximation confidence interval",
            "evidence": ["STAT:descriptive-summary"],
        }

    @staticmethod
    def _is_numeric(value: object) -> bool:
        """Check whether *value* can be interpreted as a number."""
        try:
            float(value)  # type: ignore[arg-type]
            return True
        except (TypeError, ValueError):
            return False
