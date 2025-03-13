"""Tests for web tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPStatusError, RequestError, Response

from mcp_toolbox.web.tools import (
    get_html,
    get_http_content,
    save_html,
)

# Check if optional dependencies are available
try:
    from mcp_toolbox.web.tools import search_with_tavily

    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

try:
    from mcp_toolbox.web.tools import search_with_duckduckgo

    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False


# Mock HTML content for testing
MOCK_HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a test page.</p>
</body>
</html>
"""


# Helper function to create a mock response
def create_mock_response(status_code=200, content=MOCK_HTML_CONTENT):
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = status_code
    mock_response.text = content
    mock_response.raise_for_status = MagicMock()
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = HTTPStatusError(
            "HTTP Error", request=MagicMock(), response=mock_response
        )
    return mock_response


# Test get_http_content function
@pytest.mark.asyncio
async def test_get_http_content_success():
    """Test successful HTTP request."""
    # Create a mock response
    mock_response = create_mock_response()

    # Create a mock client
    mock_client = AsyncMock()
    mock_client.request.return_value = mock_response

    # Patch the client
    with patch("mcp_toolbox.web.tools.client", mock_client):
        # Call the function
        result = await get_http_content("https://example.com")

        # Verify the client was called with the correct arguments
        mock_client.request.assert_called_once_with(
            "GET",
            "https://example.com",
            headers=None,
            params=None,
            data=None,
            timeout=60,
        )

        # Verify the result is as expected
        assert result == MOCK_HTML_CONTENT


@pytest.mark.asyncio
async def test_get_http_content_error():
    """Test HTTP request with error."""
    # Create a mock response with error status
    mock_response = create_mock_response(status_code=404)

    # Create a mock client
    mock_client = AsyncMock()
    mock_client.request.return_value = mock_response

    # Patch the client and expect an exception
    with patch("mcp_toolbox.web.tools.client", mock_client), pytest.raises(HTTPStatusError):
        await get_http_content("https://example.com")


@pytest.mark.asyncio
async def test_get_http_content_request_error():
    """Test HTTP request with request error."""
    # Create a mock client that raises a RequestError
    mock_client = AsyncMock()
    mock_client.request.side_effect = RequestError("Connection error", request=MagicMock())

    # Patch the client and expect an exception
    with patch("mcp_toolbox.web.tools.client", mock_client), pytest.raises(RequestError):
        await get_http_content("https://example.com")


# Test save_html tool
@pytest.mark.asyncio
async def test_save_html_success():
    """Test successful saving of HTML."""
    # Mock get_http_content to return HTML content
    with (
        patch("mcp_toolbox.web.tools.get_http_content", return_value=MOCK_HTML_CONTENT),
        patch("pathlib.Path.write_text") as mock_write_text,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        # Call the function
        result = await save_html("https://example.com", "/tmp/test.html")

        # Verify the result is as expected
        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert "/tmp/test.html" in result["output_path"]

        # Verify the file operations were called
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_write_text.assert_called_once_with(MOCK_HTML_CONTENT)


@pytest.mark.asyncio
async def test_save_html_network_error():
    """Test saving HTML with network error."""
    # Mock get_http_content to raise an exception
    with patch(
        "mcp_toolbox.web.tools.get_http_content",
        side_effect=Exception("Network error"),
    ):
        # Call the function
        result = await save_html("https://example.com", "/tmp/test.html")

        # Verify the result is as expected
        assert result["success"] is False
        assert "error" in result
        assert "Network error" in result["error"]


@pytest.mark.asyncio
async def test_save_html_write_error():
    """Test saving HTML with file write error."""
    # Mock get_http_content to return HTML content
    # Mock write_text to raise an exception
    with (
        patch("mcp_toolbox.web.tools.get_http_content", return_value=MOCK_HTML_CONTENT),
        patch("pathlib.Path.write_text", side_effect=Exception("Write error")),
        patch("pathlib.Path.mkdir"),
    ):
        # Call the function
        result = await save_html("https://example.com", "/tmp/test.html")

        # Verify the result is as expected
        assert result["success"] is False
        assert "error" in result
        assert "Write error" in result["error"]


# Test get_html tool
@pytest.mark.asyncio
async def test_get_html_success():
    """Test successful retrieval of HTML."""
    # Mock get_http_content to return HTML content
    with patch("mcp_toolbox.web.tools.get_http_content", return_value=MOCK_HTML_CONTENT):
        # Call the function
        result = await get_html("https://example.com")

        # Verify the result is as expected
        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert result["content"] == MOCK_HTML_CONTENT


@pytest.mark.asyncio
async def test_get_html_error():
    """Test retrieval of HTML with error."""
    # Mock get_http_content to raise an exception
    with patch(
        "mcp_toolbox.web.tools.get_http_content",
        side_effect=Exception("Network error"),
    ):
        # Call the function
        result = await get_html("https://example.com")

        # Verify the result is as expected
        assert result["success"] is False
        assert "error" in result
        assert "Network error" in result["error"]


# Test search_with_tavily tool if available
if TAVILY_AVAILABLE:

    @pytest.mark.asyncio
    async def test_search_with_tavily_success():
        """Test successful search with Tavily."""
        # Mock search results
        mock_results = [
            {"title": "Result 1", "url": "https://example.com/1", "content": "Content 1"},
            {"title": "Result 2", "url": "https://example.com/2", "content": "Content 2"},
        ]

        # Mock the Tavily client
        mock_client = AsyncMock()
        mock_client.search.return_value = {"results": mock_results}

        # Patch the AsyncTavilyClient
        with patch("mcp_toolbox.web.tools.AsyncTavilyClient", return_value=mock_client):
            # Call the function
            results = await search_with_tavily("test query")

            # Verify the client was called with the correct arguments
            mock_client.search.assert_called_once_with(
                "test query", search_depth="basic", topic="general", time_range=None
            )

            # Verify the results are as expected
            assert results == mock_results

    @pytest.mark.asyncio
    async def test_search_with_tavily_no_results():
        """Test search with Tavily with no results."""
        # Mock empty search results
        mock_results = {"results": []}

        # Mock the Tavily client
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_results

        # Patch the AsyncTavilyClient
        with patch("mcp_toolbox.web.tools.AsyncTavilyClient", return_value=mock_client):
            # Call the function
            result = await search_with_tavily("test query")

            # Verify the result is as expected
            assert result["success"] is False
            assert "error" in result
            assert "No search results found" in result["error"]


# Test search_with_duckduckgo tool if available
if DUCKDUCKGO_AVAILABLE:

    @pytest.mark.asyncio
    async def test_search_with_duckduckgo_success():
        """Test successful search with DuckDuckGo."""
        # Mock search results
        mock_results = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "Content 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "Content 2"},
        ]

        # Mock the DDGS instance
        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = mock_results

        # Patch the DDGS class and anyio.to_thread.run_sync
        with (
            patch("mcp_toolbox.web.tools.DDGS", return_value=mock_ddgs),
            patch("mcp_toolbox.web.tools.anyio.to_thread.run_sync", return_value=mock_results),
        ):
            # Call the function
            results = await search_with_duckduckgo("test query")

            # Verify the results are as expected
            assert results == mock_results

    @pytest.mark.asyncio
    async def test_search_with_duckduckgo_no_results():
        """Test search with DuckDuckGo with no results."""
        # Mock empty search results
        mock_results = []

        # Mock the DDGS instance
        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = mock_results

        # Patch the DDGS class and anyio.to_thread.run_sync
        with (
            patch("mcp_toolbox.web.tools.DDGS", return_value=mock_ddgs),
            patch("mcp_toolbox.web.tools.anyio.to_thread.run_sync", return_value=mock_results),
        ):
            # Call the function
            result = await search_with_duckduckgo("test query")

            # Verify the result is as expected
            assert result["success"] is False
            assert "error" in result
            assert "No search results found" in result["error"]
