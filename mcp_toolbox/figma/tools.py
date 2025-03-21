import json
import time
from pathlib import Path
from typing import Annotated, Any

import httpx
from pydantic import BaseModel, Field

from mcp_toolbox.app import mcp
from mcp_toolbox.config import Config


# Type definitions for request/response parameters
class ClientMeta(BaseModel):
    x: float
    y: float
    node_id: str | None = None
    node_offset: dict[str, float] | None = None


# API Client
class FigmaApiClient:
    BASE_URL = "https://api.figma.com/v1"

    def __init__(self):
        self.config = Config()

    async def get_access_token(self) -> str:
        if not self.config.figma_api_key:
            raise ValueError("No Figma API key provided. Set the FIGMA_API_KEY environment variable.")
        return self.config.figma_api_key

    async def make_request(self, path: str, method: str = "GET", data: Any = None) -> dict[str, Any]:
        token = await self.get_access_token()

        async with httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(retries=3),
            timeout=30,
        ) as client:
            headers = {"X-Figma-Token": token}
            url = f"{self.BASE_URL}{path}"

            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                figma_error = (
                    e.response.json() if e.response.content else {"status": e.response.status_code, "err": str(e)}
                )
                raise ValueError(
                    f"Figma API error: {figma_error.get('err', figma_error.get('message', str(e)))}"
                ) from e
            except httpx.RequestError as e:
                raise ValueError(f"Request error: {e!s}") from e

    def build_query_string(self, params: dict[str, Any]) -> str:
        # Filter out None values
        filtered_params = {k: v for k, v in params.items() if v is not None}

        if not filtered_params:
            return ""

        # Convert lists to comma-separated strings
        for key, value in filtered_params.items():
            if isinstance(value, list):
                filtered_params[key] = ",".join(map(str, value))

        # Build query string
        query_parts = [f"{k}={v}" for k, v in filtered_params.items()]
        return "?" + "&".join(query_parts)


# Cache Manager
class CacheManager:
    def __init__(self):
        self.config = Config()
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save_to_cache(self, filename: str, data: Any) -> str:
        file_path = self.cache_dir / filename
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return str(file_path)


# Initialize API client and cache manager
api_client = FigmaApiClient()
cache_manager = CacheManager()


# Tool implementations
@mcp.tool(description="Get a Figma file by key")
async def figma_get_file(
    file_key: Annotated[str, Field(description="The key of the file to get")],
    version: Annotated[str | None, Field(default=None, description="A specific version ID to get")] = None,
    depth: Annotated[int | None, Field(default=None, description="Depth of nodes to return 1-4")] = None,
    branch_data: Annotated[bool | None, Field(default=None, description="Include branch data if true")] = None,
) -> dict[str, Any]:
    """Get a Figma file by key."""
    params = {"version": version, "depth": depth, "branch_data": branch_data}

    query_string = api_client.build_query_string(params)
    result = await api_client.make_request(f"/files/{file_key}{query_string}")

    # Save to cache
    try:
        filename = f"file_{file_key}_{int(time.time() * 1000)}.json"
        file_path = cache_manager.save_to_cache(filename, result)
        return {
            "file_path": file_path,
            "message": "File data saved to local cache. Use this file path to access the complete data.",
        }
    except Exception:
        # If saving to cache fails, return original result
        return result


@mcp.tool(description="Get specific nodes from a Figma file.")
async def figma_get_file_nodes(
    file_key: Annotated[str, Field(description="The key of the file to get nodes from")],
    node_ids: Annotated[list[str], Field(description="Array of node IDs to get")],
    depth: Annotated[int | None, Field(default=None, description="Depth of nodes to return 1-4")] = None,
    version: Annotated[str | None, Field(default=None, description="A specific version ID to get")] = None,
) -> dict[str, Any]:
    """Get specific nodes from a Figma file."""
    params = {"ids": node_ids, "depth": depth, "version": version}

    query_string = api_client.build_query_string(params)
    result = await api_client.make_request(f"/files/{file_key}/nodes{query_string}")

    # Save to cache
    try:
        filename = f"file_nodes_{file_key}_{int(time.time() * 1000)}.json"
        file_path = cache_manager.save_to_cache(filename, result)
        return {
            "file_path": file_path,
            "message": "File nodes data saved to local cache. Use this file path to access the complete data.",
        }
    except Exception:
        # If saving to cache fails, return original result
        return result


@mcp.tool(description="Get images for nodes in a Figma file.")
async def figma_get_image(
    file_key: Annotated[str, Field(description="The key of the file to get images from")],
    ids: Annotated[list[str], Field(description="Array of node IDs to render")],
    scale: Annotated[float | None, Field(default=None, description="Scale factor to render at 0.01-4")] = None,
    format_type: Annotated[str | None, Field(default=None, description="Image format jpg/png/svg/pdf")] = None,
    svg_include_id: Annotated[bool | None, Field(default=None, description="Include IDs in SVG output")] = None,
    svg_simplify_stroke: Annotated[
        bool | None, Field(default=None, description="Simplify strokes in SVG output")
    ] = None,
    use_absolute_bounds: Annotated[bool | None, Field(default=None, description="Use absolute bounds")] = None,
) -> dict[str, Any]:
    """Get images for nodes in a Figma file."""
    params = {
        "ids": ids,
        "scale": scale,
        "format": format_type,
        "svg_include_id": svg_include_id,
        "svg_simplify_stroke": svg_simplify_stroke,
        "use_absolute_bounds": use_absolute_bounds,
    }

    query_string = api_client.build_query_string(params)
    return await api_client.make_request(f"/images/{file_key}{query_string}")


@mcp.tool(description="Get URLs for images used in a Figma file.")
async def figma_get_image_fills(
    file_key: Annotated[str, Field(description="The key of the file to get image fills from")],
) -> dict[str, Any]:
    """Get URLs for images used in a Figma file."""
    return await api_client.make_request(f"/files/{file_key}/images")


@mcp.tool(description="Get comments on a Figma file.")
async def figma_get_comments(
    file_key: Annotated[str, Field(description="The key of the file to get comments from")],
) -> dict[str, Any]:
    """Get comments on a Figma file."""
    return await api_client.make_request(f"/files/{file_key}/comments")


@mcp.tool(description="Post a comment on a Figma file.")
async def figma_post_comment(
    file_key: Annotated[str, Field(description="The key of the file to comment on")],
    message: Annotated[str, Field(description="Comment message text")],
    client_meta: Annotated[
        dict[str, Any] | None, Field(default=None, description="Position of the comment x/y/node_id/node_offset")
    ] = None,
    comment_id: Annotated[str | None, Field(default=None, description="ID of comment to reply to")] = None,
) -> dict[str, Any]:
    """Post a comment on a Figma file."""
    comment_data = {"message": message}

    if client_meta:
        comment_data["client_meta"] = client_meta

    if comment_id:
        comment_data["comment_id"] = comment_id

    return await api_client.make_request(f"/files/{file_key}/comments", "POST", comment_data)


@mcp.tool(description="Delete a comment from a Figma file.")
async def figma_delete_comment(
    file_key: Annotated[str, Field(description="The key of the file to delete a comment from")],
    comment_id: Annotated[str, Field(description="ID of the comment to delete")],
) -> dict[str, Any]:
    """Delete a comment from a Figma file."""
    return await api_client.make_request(f"/files/{file_key}/comments/{comment_id}", "DELETE")


@mcp.tool(description="Get projects for a team.")
async def figma_get_team_projects(
    team_id: Annotated[str, Field(description="The team ID")],
    page_size: Annotated[int | None, Field(default=None, description="Number of items per page")] = None,
    cursor: Annotated[str | None, Field(default=None, description="Cursor for pagination")] = None,
) -> dict[str, Any]:
    """Get projects for a team."""
    params = {"page_size": page_size, "cursor": cursor}

    query_string = api_client.build_query_string(params)
    return await api_client.make_request(f"/teams/{team_id}/projects{query_string}")


@mcp.tool(description="Get files for a project.")
async def figma_get_project_files(
    project_id: Annotated[str, Field(description="The project ID")],
    page_size: Annotated[int | None, Field(default=None, description="Number of items per page")] = None,
    cursor: Annotated[str | None, Field(default=None, description="Cursor for pagination")] = None,
    branch_data: Annotated[bool | None, Field(default=None, description="Include branch data if true")] = None,
) -> dict[str, Any]:
    """Get files for a project."""
    params = {"page_size": page_size, "cursor": cursor, "branch_data": branch_data}

    query_string = api_client.build_query_string(params)
    return await api_client.make_request(f"/projects/{project_id}/files{query_string}")


@mcp.tool(description="Get components for a team.")
async def figma_get_team_components(
    team_id: Annotated[str, Field(description="The team ID")],
    page_size: Annotated[int | None, Field(default=None, description="Number of items per page")] = None,
    cursor: Annotated[str | None, Field(default=None, description="Cursor for pagination")] = None,
) -> dict[str, Any]:
    """Get components for a team."""
    params = {"page_size": page_size, "cursor": cursor}

    query_string = api_client.build_query_string(params)
    return await api_client.make_request(f"/teams/{team_id}/components{query_string}")


@mcp.tool(description="Get components from a file.")
async def figma_get_file_components(
    file_key: Annotated[str, Field(description="The key of the file to get components from")],
) -> dict[str, Any]:
    """Get components from a file."""
    return await api_client.make_request(f"/files/{file_key}/components")


@mcp.tool(description="Get a component by key.")
async def figma_get_component(key: Annotated[str, Field(description="The component key")]) -> dict[str, Any]:
    """Get a component by key."""
    return await api_client.make_request(f"/components/{key}")


@mcp.tool(description="Get component sets for a team.")
async def figma_get_team_component_sets(
    team_id: Annotated[str, Field(description="The team ID")],
    page_size: Annotated[int | None, Field(default=None, description="Number of items per page")] = None,
    cursor: Annotated[str | None, Field(default=None, description="Cursor for pagination")] = None,
) -> dict[str, Any]:
    """Get component sets for a team."""
    params = {"page_size": page_size, "cursor": cursor}

    query_string = api_client.build_query_string(params)
    return await api_client.make_request(f"/teams/{team_id}/component_sets{query_string}")


@mcp.tool(description="Get styles for a team.")
async def figma_get_team_styles(
    team_id: Annotated[str, Field(description="The team ID")],
    page_size: Annotated[int | None, Field(default=None, description="Number of items per page")] = None,
    cursor: Annotated[str | None, Field(default=None, description="Cursor for pagination")] = None,
) -> dict[str, Any]:
    """Get styles for a team."""
    params = {"page_size": page_size, "cursor": cursor}

    query_string = api_client.build_query_string(params)
    return await api_client.make_request(f"/teams/{team_id}/styles{query_string}")


@mcp.tool(description="Get styles from a file.")
async def figma_get_file_styles(
    file_key: Annotated[str, Field(description="The key of the file to get styles from")],
) -> dict[str, Any]:
    """Get styles from a file."""
    return await api_client.make_request(f"/files/{file_key}/styles")


@mcp.tool(description="Get a style by key.")
async def figma_get_style(key: Annotated[str, Field(description="The style key")]) -> dict[str, Any]:
    """Get a style by key."""
    return await api_client.make_request(f"/styles/{key}")
