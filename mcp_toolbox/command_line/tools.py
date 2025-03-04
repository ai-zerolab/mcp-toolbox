"""Command line execution tools for MCP-Toolbox."""

import asyncio
import contextlib
import os
from pathlib import Path
from typing import Any

from mcp_toolbox.app import mcp


@mcp.tool(
    description="Execute a command line instruction. Args: command (required, The command to execute as a list of strings), timeout_seconds (optional, Maximum execution time in seconds), working_dir (optional, Directory to execute the command in)"
)
async def execute_command(
    command: list[str],
    timeout_seconds: int = 30,
    working_dir: str | None = None,
) -> dict[str, Any]:
    """Execute a command line instruction.

    Args:
        command: The command to execute as a list of strings
        timeout_seconds: Optional. Maximum execution time in seconds (default: 30)
        working_dir: Optional. Directory to execute the command in

    Returns:
        Dictionary containing stdout, stderr, and return code
    """
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
