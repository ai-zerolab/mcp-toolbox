import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_toolbox.command_line.tools import execute_command


# Mock for asyncio.create_subprocess_exec
class MockProcess:
    def __init__(self, stdout=b"", stderr=b"", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.communicate = AsyncMock(return_value=(stdout, stderr))
        self.kill = MagicMock()


@pytest.mark.asyncio
async def test_execute_command_success():
    """Test successful command execution."""
    # Mock process with successful execution
    mock_process = MockProcess(stdout=b"test output", stderr=b"", returncode=0)

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        result = await execute_command(["echo", "test"])

        # Verify subprocess was called with correct arguments
        mock_exec.assert_called_once()

        # Verify the result contains expected fields
        assert "stdout" in result
        assert "stderr" in result
        assert "return_code" in result
        assert result["stdout"] == "test output"
        assert result["stderr"] == ""
        assert result["return_code"] == 0


@pytest.mark.asyncio
async def test_execute_command_error():
    """Test command execution with error."""
    # Mock process with error
    mock_process = MockProcess(stdout=b"", stderr=b"error message", returncode=1)

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        result = await execute_command(["invalid_command"])

        # Verify subprocess was called
        mock_exec.assert_called_once()

        # Verify the result contains expected fields
        assert "stdout" in result
        assert "stderr" in result
        assert "return_code" in result
        assert result["stdout"] == ""
        assert result["stderr"] == "error message"
        assert result["return_code"] == 1


@pytest.mark.asyncio
async def test_execute_command_timeout():
    """Test command execution timeout."""
    # Mock process that will time out
    mock_process = MockProcess()
    mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        result = await execute_command(["sleep", "100"], timeout_seconds=1)

        # Verify subprocess was called
        mock_exec.assert_called_once()

        # Verify process was killed
        mock_process.kill.assert_called_once()

        # Verify the result contains expected fields
        assert "error" in result
        assert "timed out" in result["error"]
        assert result["return_code"] == 124  # Timeout return code


@pytest.mark.asyncio
async def test_execute_command_exception():
    """Test exception during command execution."""
    with patch("asyncio.create_subprocess_exec", side_effect=Exception("Test exception")) as mock_exec:
        result = await execute_command(["echo", "test"])

        # Verify subprocess was called
        mock_exec.assert_called_once()

        # Verify the result contains expected fields
        assert "error" in result
        assert "Failed to execute command" in result["error"]
        assert result["return_code"] == 1


@pytest.mark.asyncio
async def test_execute_command_empty():
    """Test execution with empty command."""
    result = await execute_command([])

    # Verify the result contains expected fields
    assert "error" in result
    assert "Command cannot be empty" in result["error"]
    assert result["return_code"] == 1


@pytest.mark.asyncio
async def test_execute_command_with_working_dir():
    """Test command execution with working directory."""
    # Mock process with successful execution
    mock_process = MockProcess(stdout=b"test output", stderr=b"", returncode=0)
    test_dir = "/test_dir"  # Using a non-tmp directory for testing

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        result = await execute_command(["echo", "test"], working_dir=test_dir)

        # Verify subprocess was called with correct arguments
        mock_exec.assert_called_once()
        _, kwargs = mock_exec.call_args
        assert kwargs["cwd"] == Path(test_dir)

        # Verify the result contains expected fields
        assert result["return_code"] == 0


@pytest.mark.asyncio
async def test_execute_command_with_tilde_in_working_dir():
    """Test command execution with tilde in working directory."""
    # Mock process with successful execution
    mock_process = MockProcess(stdout=b"test output", stderr=b"", returncode=0)
    test_dir = "~/test_dir"  # Using tilde in path

    with (
        patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec,
        patch("pathlib.Path.expanduser", return_value=Path("/home/user/test_dir")) as mock_expanduser,
    ):
        result = await execute_command(["echo", "test"], working_dir=test_dir)

        # Verify expanduser was called
        mock_expanduser.assert_called_once()

        # Verify subprocess was called with correct arguments
        mock_exec.assert_called_once()
        _, kwargs = mock_exec.call_args
        assert kwargs["cwd"] == Path("/home/user/test_dir")

        # Verify the result contains expected fields
        assert result["return_code"] == 0
