import functools
from pathlib import Path
from typing import Any, Literal

import anyio
from duckduckgo_search import DDGS
from httpx import AsyncClient
from tavily import AsyncTavilyClient

from mcp_toolbox.app import mcp
from mcp_toolbox.config import Config

client = AsyncClient(
    follow_redirects=True,
)


async def get_http_content(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    data: dict[str, str] | None = None,
    timeout: int = 60,
) -> str:
    response = await client.request(
        method,
        url,
        headers=headers,
        params=params,
        data=data,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


@mcp.tool(
    description="Save HTML from a URL. Args: url (required, The URL to save), output_path (required, The path to save the HTML)",
)
async def save_html(url: str, output_path: str) -> dict[str, Any]:
    output_path: Path = Path(output_path).expanduser().resolve().absolute()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        content = await get_http_content(url)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save HTML: {e!s}",
        }

    try:
        output_path.write_text(content)
        return {
            "success": True,
            "url": url,
            "output_path": output_path.as_posix(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save HTML: {e!s}",
        }


@mcp.tool(
    description="Get HTML from a URL. Args: url (required, The URL to get)",
)
async def get_html(url: str) -> dict[str, Any]:
    try:
        content = await get_http_content(url)
        return {
            "success": True,
            "url": url,
            "content": content,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get HTML: {e!s}",
        }


if Config().tavily_api_key:

    @mcp.tool(
        description="Search with Tavily. Args: query (required, The search query), search_deep (optional, The search depth), topic (optional, The topic), time_range (optional, The time range)",
    )
    async def search_with_tavily(
        query: str,
        search_deep: Literal["basic", "advanced"] = "basic",
        topic: Literal["general", "news"] = "general",
        time_range: (Literal["day", "week", "month", "year", "d", "w", "m", "y"] | None) = None,
    ) -> list[dict[str, Any]]:
        client = AsyncTavilyClient(Config().tavily_api_key)
        results = await client.search(query, search_depth=search_deep, topic=topic, time_range=time_range)
        if not results["results"]:
            return {
                "success": False,
                "error": "No search results found.",
            }
        return results["results"]


if Config().duckduckgo_api_key:

    @mcp.tool(
        description="Search with DuckDuckGo. Args: query (required, The search query), max_results (optional, The maximum number of results)",
    )
    async def search_with_duckduckgo(query: str, max_results: int = 10) -> list[dict[str, Any]]:
        ddg = DDGS(Config().duckduckgo_api_key)
        search = functools.partial(ddg.text, max_results=max_results)
        results = await anyio.to_thread.run_sync(search, query)
        if len(results) == 0:
            return {
                "success": False,
                "error": "No search results found.",
            }
        return results
