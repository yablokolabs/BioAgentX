from prometheus_client import Counter, Histogram, generate_latest

WORKFLOW_RUNS = Counter("bioagentx_workflow_runs_total", "BioAgentX workflow runs", ["status"])
TOOL_CALLS = Counter("bioagentx_tool_calls_total", "Tool calls", ["tool", "status"])
RETRIEVALS = Counter("bioagentx_retrievals_total", "RAG retrievals", ["backend"])
WORKFLOW_LATENCY = Histogram("bioagentx_workflow_latency_seconds", "Workflow latency")


def metrics_bytes() -> bytes:
    return generate_latest()
