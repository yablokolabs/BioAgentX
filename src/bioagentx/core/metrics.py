from prometheus_client import Counter, Histogram, generate_latest

WORKFLOW_RUNS = Counter("bioagentx_workflow_runs_total", "Completed workflow runs by outcome.", ["status"])
TOOL_CALLS = Counter("bioagentx_tool_calls_total", "Tool invocations by tool and status.", ["tool", "status"])
RETRIEVALS = Counter("bioagentx_retrievals_total", "RAG retrieval requests by backend.", ["backend"])
WORKFLOW_LATENCY = Histogram("bioagentx_workflow_latency_seconds", "End-to-end workflow latency.")


def metrics_bytes() -> bytes:
    """Serialize all Prometheus metrics to the exposition format."""
    return generate_latest()
