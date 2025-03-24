from typing import Annotated

from pydantic import Field

from mcp_toolbox.app import mcp
from mcp_toolbox.log import logger


@mcp.tool(
    description="Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed."
)
async def think(
    thought: Annotated[str, Field(description="A thought to think about.")],
) -> dict[str, str]:
    """
    see: https://www.anthropic.com/engineering/claude-think-tool
    """

    return {
        "thought": thought,
    }


try:
    from mcp_toolbox.enhance.memory import LocalMemory, get_current_session_memory
except ImportError:
    logger.error(
        "Memory tools are not available. Please install the required dependencies. e.g. `pip install mcp-toolbox[enhance]`"
    )
else:

    @mcp.tool(description="Get the current session id.")
    def get_session_id() -> dict[str, str]:
        memory: LocalMemory = get_current_session_memory()
        return {"session_id": memory.session_id}

    @mcp.tool(description="Store a memory in the memory database.")
    def remember(
        brief: Annotated[str, Field(description="The brief information of the memory.")],
        detail: Annotated[str, Field(description="The detailed information of the brief text.")],
    ) -> dict[str, str]:
        memory: LocalMemory = get_current_session_memory()
        memory.store(brief, detail)
        return {
            "session_id": memory.session_id,
            "brief": brief,
            "detail": detail,
        }

    @mcp.tool(description="Query a memory from the memory database.")
    def recall(
        query: Annotated[str, Field(description="The query to search in the memory database.")],
        top_k: Annotated[
            int,
            Field(
                description="The maximum number of results to return. Default to 5.",
                default=5,
            ),
        ] = 5,
        cross_session: Annotated[
            bool,
            Field(
                description="Whether to search across all sessions. Default to True.",
                default=True,
            ),
        ] = True,
        session_id: Annotated[
            str | None,
            Field(
                description="The session id of the memory. If not provided, the current session id will be used.",
                default=None,
            ),
        ] = None,
    ) -> list[dict[str, str]]:
        if session_id:
            memory = LocalMemory.use_session(session_id)
        else:
            memory: LocalMemory = get_current_session_memory()
        results = memory.query(query, top_k=top_k, cross_session=cross_session)
        return [r.model_dump() for r in results]

    @mcp.tool(description="Clear all memories in the memory database.")
    def forget() -> dict[str, str]:
        memory: LocalMemory = get_current_session_memory()
        memory.clear()
        return {"message": "All memories are cleared."}
