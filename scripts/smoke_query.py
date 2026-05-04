import asyncio

import httpx


async def main() -> None:
    async with httpx.AsyncClient(base_url="http://localhost:8080", timeout=20) as client:
        response = await client.post(
            "/query",
            json={"query": "Explain EGFR lung cancer therapy evidence and clinical trials."},
        )
        response.raise_for_status()
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())
