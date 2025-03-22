"""Command line execution tools for MCP-Toolbox."""

import asyncio
import contextlib
import os
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field

from mcp_toolbox.app import mcp


@mcp.tool(description="Execute a command line instruction.")
async def execute_command(
    command: Annotated[list[str], Field(description="The command to execute as a list of strings")],
    timeout_seconds: Annotated[int, Field(default=30, description="Maximum execution time in seconds")] = 30,
    working_dir: Annotated[str | None, Field(default=None, description="Directory to execute the command in")] = None,
) -> dict[str, Any]:
    """Execute a command line instruction."""
    if not command:
        return {
            "error": "Command cannot be empty",
            "stdout": "",
            "stderr": "",
            "return_code": 1,
        }

    try:
        # Expand user home directory in working_dir if provided
        expanded_working_dir = Path(working_dir).expanduser() if working_dir else working_dir

        # Create subprocess with current environment
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ,
            cwd=expanded_working_dir,
        )

        try:
            # Wait for the process with timeout
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

            return {
                "stdout": stdout_str,
                "stderr": stderr_str,
                "return_code": process.returncode,
            }

        except asyncio.TimeoutError:
            # Kill the process if it times out
            with contextlib.suppress(ProcessLookupError):
                process.kill()

            return {
                "error": f"Command execution timed out after {timeout_seconds} seconds",
                "stdout": "",
                "stderr": "",
                "return_code": 124,  # Standard timeout return code
            }

    except Exception as e:
        return {
            "error": f"Failed to execute command: {e!s}",
            "stdout": "",
            "stderr": "",
            "return_code": 1,
        }
