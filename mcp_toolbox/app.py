from mcp.server.fastmcp import FastMCP

from mcp_toolbox.config import Config

mcp = FastMCP("email")
config = Config()


# Import tools to register them with the MCP server
if config.enable_commond_tools:
    import mcp_toolbox.command_line.tools
if config.enable_file_ops_tools:
    import mcp_toolbox.file_ops.tools
if config.enable_audio_tools:
    import mcp_toolbox.audio.tools
if config.figma_api_key:
    import mcp_toolbox.figma.tools
import mcp_toolbox.markitdown.tools  # noqa: E402
import mcp_toolbox.web.tools  # noqa: E402
import mcp_toolbox.xiaoyuzhoufm.tools  # noqa: E402, F401

# TODO: Add prompt for toolbox's tools
