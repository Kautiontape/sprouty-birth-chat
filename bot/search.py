import logging
import os

import httpx

log = logging.getLogger(__name__)

SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")


async def web_search(query: str, num: int = 5) -> str:
    if not SERPER_API_KEY:
        return "Web search is not configured (no SERPER_API_KEY)."

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": num},
                headers={
                    "X-API-KEY": SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        log.exception("Search failed for: %s", query)
        return "Search failed. Try again."

    results = data.get("organic", [])
    if not results:
        return "No results found."

    lines = []
    for r in results:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        link = r.get("link", "")
        lines.append(f"**{title}**\n{snippet}\n{link}")

    return "\n\n".join(lines)
