import functools
from pathlib import Path
from typing import Annotated, Any, Literal

import anyio
from duckduckgo_search import DDGS
from httpx import AsyncClient
from pydantic import Field
from tavily import AsyncTavilyClient

from mcp_toolbox.app import mcp
from mcp_toolbox.config import Config

client = AsyncClient(
    follow_redirects=True,
)


async def get_http_content(
    url: Annotated[str, Field(description="The URL to request")],
    method: Annotated[str, Field(default="GET", description="HTTP method to use")] = "GET",
    headers: Annotated[dict[str, str] | None, Field(default=None, description="Optional HTTP headers")] = None,
    params: Annotated[dict[str, str] | None, Field(default=None, description="Optional query parameters")] = None,
    data: Annotated[dict[str, str] | None, Field(default=None, description="Optional request body data")] = None,
    timeout: Annotated[int, Field(default=60, description="Request timeout in seconds")] = 60,
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
    description="Save HTML from a URL.",
)
async def save_html(
    url: Annotated[str, Field(description="The URL to save")],
    output_path: Annotated[str, Field(description="The path to save the HTML")],
) -> dict[str, Any]:
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
    description="Get HTML from a URL.",
)
async def get_html(url: Annotated[str, Field(description="The URL to get")]) -> dict[str, Any]:
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
        description="Search with Tavily.",
    )
    async def search_with_tavily(
        query: Annotated[str, Field(description="The search query")],
        search_deep: Annotated[
            Literal["basic", "advanced"], Field(default="basic", description="The search depth")
        ] = "basic",
        topic: Annotated[Literal["general", "news"], Field(default="general", description="The topic")] = "general",
        time_range: Annotated[
            Literal["day", "week", "month", "year", "d", "w", "m", "y"] | None,
            Field(default=None, description="The time range"),
        ] = None,
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
        description="Search with DuckDuckGo.",
    )
    async def search_with_duckduckgo(
        query: Annotated[str, Field(description="The search query")],
        max_results: Annotated[int, Field(default=10, description="The maximum number of results")] = 10,
    ) -> list[dict[str, Any]]:
        ddg = DDGS(Config().duckduckgo_api_key)
        search = functools.partial(ddg.text, max_results=max_results)
        results = await anyio.to_thread.run_sync(search, query)
        if len(results) == 0:
            return {
                "success": False,
                "error": "No search results found.",
            }
        return results
