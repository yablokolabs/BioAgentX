import asyncio
import os

import httpx

_DEFAULT_BASE_URL = "http://localhost:8080"


async def main() -> None:
    """Send a smoke-test query to the running BioAgentX instance."""
    base_url = os.environ.get("BIOAGENTX_URL", _DEFAULT_BASE_URL)
    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        response = await client.post(
            "/query",
            json={"query": "Explain EGFR lung cancer therapy evidence and clinical trials."},
        )
        response.raise_for_status()
        import json

        print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
