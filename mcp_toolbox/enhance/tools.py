from typing import Annotated

from pydantic import Field

from mcp_toolbox.app import mcp


@mcp.tool(
    description="Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed."
)
async def think(
    thought: Annotated[str, Field(description="A thought to think about.")],
) -> dict[str, str]:
    return {
        "thought": thought,
    }
