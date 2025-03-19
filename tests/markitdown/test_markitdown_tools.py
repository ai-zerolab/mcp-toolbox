"""Tests for Markitdown tools."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_toolbox.markitdown.tools import (
    convert_file_to_markdown,
    convert_url_to_markdown,
    md,
)


# Mock for MarkItDown.convert method
@pytest.fixture
def mock_markitdown_convert():
    """Mock for MarkItDown.convert method."""
    with patch.object(md, "convert") as mock_convert:
        # Set up the mock to return a result with text_content
        mock_result = MagicMock()
        mock_result.text_content = "# Converted Markdown\n\nThis is converted content."
        mock_convert.return_value = mock_result
        yield mock_convert


@pytest.fixture
def mock_markitdown_convert_url():
    """Mock for MarkItDown.convert method."""
    with patch.object(md, "convert_url") as mock_convert:
        # Set up the mock to return a result with text_content
        mock_result = MagicMock()
        mock_result.text_content = "# Converted Markdown\n\nThis is converted content."
        mock_convert.return_value = mock_result
        yield mock_convert


# Test convert_file_to_markdown function
@pytest.mark.asyncio
async def test_convert_file_to_markdown_success(mock_markitdown_convert):
    """Test successful file conversion."""
    # Mock file operations
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.write_text") as mock_write_text,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        # Call the function
        result = await convert_file_to_markdown("input.txt", "output.md")

        # Verify the output file was written with the converted content
        mock_write_text.assert_called_once_with("# Converted Markdown\n\nThis is converted content.")

        # Verify the output directory was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify the result is as expected
        assert result["success"] is True
        assert "input.txt" in result["input_file"]
        assert "output.md" in result["output_file"]


@pytest.mark.asyncio
async def test_convert_file_to_markdown_file_not_found():
    """Test file conversion when input file doesn't exist."""
    # Mock file operations
    with patch("pathlib.Path.is_file", return_value=False):
        # Call the function
        result = await convert_file_to_markdown("nonexistent.txt", "output.md")

        # Verify the result is as expected
        assert result["success"] is False
        assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_convert_file_to_markdown_exception(mock_markitdown_convert):
    """Test file conversion when an exception occurs."""
    # Set up the mock to raise an exception
    mock_markitdown_convert.side_effect = Exception("Conversion error")

    # Mock file operations
    with (
        patch("pathlib.Path.is_file", return_value=True),
        patch("pathlib.Path.read_text", return_value="Original content"),
        patch("pathlib.Path.mkdir"),
    ):
        # Call the function and expect an exception
        with pytest.raises(Exception) as excinfo:
            await convert_file_to_markdown("input.txt", "output.md")

        # Verify the exception message
        assert "Conversion error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_convert_url_to_markdown_success(mock_markitdown_convert_url):
    """Test successful file conversion."""
    # Mock file operations
    with (
        patch("pathlib.Path.write_text") as mock_write_text,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        # Call the function
        result = await convert_url_to_markdown("https://example.com", "output.md")

        # Verify the output file was written with the converted content
        mock_write_text.assert_called_once_with("# Converted Markdown\n\nThis is converted content.")

        # Verify the output directory was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify the result is as expected
        assert result["success"] is True
        assert "https://example.com" in result["url"]
        assert "output.md" in result["output_file"]
