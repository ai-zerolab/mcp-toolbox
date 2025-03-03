from mcp.server.fastmcp import FastMCP

mcp = FastMCP("email")

# Import tools to register them with the MCP server
import mcp_toolbox.command_line.tools  # noqa: E402
import mcp_toolbox.figma.tools  # noqa: E402, F401
