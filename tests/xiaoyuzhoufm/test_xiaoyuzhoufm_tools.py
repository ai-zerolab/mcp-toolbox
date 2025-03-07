"""Tests for XiaoyuZhouFM tools."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_toolbox.xiaoyuzhoufm.tools import XiaoyuZhouFMCrawler, xiaoyuzhoufm_download


# Helper function to load mock data
def load_mock_data(filename):
    mock_dir = Path(__file__).parent.parent / "mock" / "xiaoyuzhoufm"
    mock_dir.mkdir(parents=True, exist_ok=True)
    file_path = mock_dir / filename

    if not file_path.exists():
        # Create empty mock data if it doesn't exist
        mock_data = {"mock": "data"}
        with open(file_path, "w") as f:
            json.dump(mock_data, f)

    with open(file_path) as f:
        return json.load(f)


# Mock HTML content with audio URL
MOCK_HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:audio" content="https://media.example.com/podcasts/episode123.m4a">
    <title>Test Episode</title>
</head>
<body>
    <h1>Test Episode</h1>
</body>
</html>
"""


# Test XiaoyuZhouFMCrawler.extract_audio_url method
@pytest.mark.asyncio
async def test_extract_audio_url():
    # Create a mock response
    mock_response = MagicMock()
    mock_response.text = MOCK_HTML_CONTENT
    mock_response.raise_for_status = AsyncMock()

    # Create a mock client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get.return_value = mock_response

    # Patch httpx.AsyncClient
    with patch("httpx.AsyncClient", return_value=mock_client):
        crawler = XiaoyuZhouFMCrawler()
        audio_url = await crawler.extract_audio_url("https://www.xiaoyuzhoufm.com/episode/test")

    # Assert the audio URL is extracted correctly
    assert audio_url == "https://media.example.com/podcasts/episode123.m4a"


# Test XiaoyuZhouFMCrawler.download_audio method
@pytest.mark.asyncio
async def test_download_audio(tmp_path):
    # Create a mock response with binary content
    mock_response = MagicMock()
    mock_response.content = b"test audio content"
    mock_response.raise_for_status = AsyncMock()

    # Create a mock client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get.return_value = mock_response

    # Patch httpx.AsyncClient
    with patch("httpx.AsyncClient", return_value=mock_client):
        crawler = XiaoyuZhouFMCrawler()
        output_path = str(tmp_path / "test_audio.m4a")
        downloaded_path = await crawler.download_audio("https://media.example.com/podcasts/episode123.m4a", output_path)

    # Assert the file was downloaded correctly
    assert downloaded_path == output_path
    assert os.path.exists(output_path)
    with open(output_path, "rb") as f:
        content = f.read()
        assert content == b"test audio content"


# Test xiaoyuzhoufm_download tool
@pytest.mark.asyncio
async def test_xiaoyuzhoufm_download():
    # Mock the crawler methods
    with (
        patch("mcp_toolbox.xiaoyuzhoufm.tools.crawler.extract_audio_url") as mock_extract,
        patch("mcp_toolbox.xiaoyuzhoufm.tools.crawler.download_audio") as mock_download,
    ):
        # Set up the mocks
        mock_extract.return_value = "https://media.example.com/podcasts/episode123.m4a"
        mock_download.return_value = "/tmp/test/test.m4a"

        # Call the tool
        result = await xiaoyuzhoufm_download("https://www.xiaoyuzhoufm.com/episode/test", "/tmp/test")

        # Assert the result
        assert result["audio_url"] == "https://media.example.com/podcasts/episode123.m4a"
        assert result["downloaded_path"] == "/tmp/test/test.m4a"
        assert "Successfully downloaded" in result["message"]

        # Verify the mocks were called correctly
        mock_extract.assert_called_once_with("https://www.xiaoyuzhoufm.com/episode/test")
        # The output path should be constructed from the output_dir and episode ID
        mock_download.assert_called_once_with("https://media.example.com/podcasts/episode123.m4a", "/tmp/test/test.m4a")


# Test xiaoyuzhoufm_download tool with invalid URL
@pytest.mark.asyncio
async def test_xiaoyuzhoufm_download_invalid_url():
    # Call the tool with an invalid URL
    result = await xiaoyuzhoufm_download("https://invalid-url.com", "/tmp/test")

    # Assert the result contains an error
    assert "error" in result
    assert "Invalid XiaoyuZhouFM URL" in result["message"]


# Test xiaoyuzhoufm_download tool with extraction error
@pytest.mark.asyncio
async def test_xiaoyuzhoufm_download_extraction_error():
    # Mock the crawler methods to raise an error
    with patch("mcp_toolbox.xiaoyuzhoufm.tools.crawler.extract_audio_url") as mock_extract:
        # Set up the mock to raise an error
        mock_extract.side_effect = ValueError("Could not find audio URL")

        # Call the tool
        result = await xiaoyuzhoufm_download("https://www.xiaoyuzhoufm.com/episode/test", "/tmp/test")

        # Assert the result contains an error
        assert "error" in result
        assert "Could not find audio URL" in result["error"]
        assert "Failed to download podcast" in result["message"]
