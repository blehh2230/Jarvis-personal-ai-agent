import asyncio
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


load_dotenv()

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def _search_web_sync(
    query: str,
    max_results: int = 5,
) -> list[dict]:
    """Call Tavily's search API and return normalized results."""

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is missing from the root .env file."
        )

    if not query or not query.strip():
        raise ValueError("The search query cannot be empty.")

    max_results = max(1, min(max_results, 10))

    payload = {
        "query": query.strip(),
        "topic": "general",
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }

    request = Request(
        TAVILY_SEARCH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

    except HTTPError as exc:
        if exc.code in (401, 403):
            raise RuntimeError(
                "Tavily authentication failed. Check TAVILY_API_KEY."
            ) from exc

        raise RuntimeError(
            f"Tavily search returned HTTP {exc.code}."
        ) from exc

    except (URLError, TimeoutError) as exc:
        raise RuntimeError(
            "Could not connect to Tavily. Check your internet connection."
        ) from exc

    results = []

    for item in data.get("results", []):
        url = item.get("url")
        title = item.get("title")
        content = item.get("content")

        # Do not accept incomplete source records.
        if not url or not title or not content:
            continue

        results.append(
            {
                "title": title,
                "url": url,
                "content": content,
                "score": item.get("score"),
            }
        )

    return results


async def search_web(
    query: str,
    max_results: int = 5,
) -> list[dict]:
    """Search the web without blocking FastAPI's event loop."""

    return await asyncio.to_thread(
        _search_web_sync,
        query,
        max_results,
    )