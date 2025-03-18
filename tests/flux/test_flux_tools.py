"""Tests for Flux API tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_toolbox.flux.api import ApiException
from mcp_toolbox.flux.tools import flux_generate_image


@pytest.fixture
def mock_config():
    """Mock Config with BFL_API_KEY."""
    with patch("mcp_toolbox.flux.tools.Config") as mock_config:
        config_instance = MagicMock()
        config_instance.bfl_api_key = "test_api_key"
        mock_config.return_value = config_instance
        yield mock_config


@pytest.fixture
def mock_image_request():
    """Mock ImageRequest class."""
    with patch("mcp_toolbox.flux.tools.ImageRequest") as mock_class:
        instance = AsyncMock()
        instance.request = AsyncMock()
        instance.retrieve = AsyncMock(return_value={"sample": "https://example.com/image.png"})
        instance.get_url = AsyncMock(return_value="https://example.com/image.png")
        instance.save = AsyncMock(return_value="/path/to/saved/image.png")
        mock_class.return_value = instance
        yield mock_class, instance


@pytest.mark.asyncio
async def test_flux_generate_image_success(mock_config, mock_image_request):
    """Test successful image generation."""
    mock_class, mock_instance = mock_image_request

    result = await flux_generate_image(
        prompt="a beautiful landscape",
        output_dir="/tmp/images",
        model_name="flux.1.1-pro",
        width=512,
        height=512,
        seed=42,
    )

    # Check that ImageRequest was created with correct parameters
    mock_class.assert_called_once_with(
        prompt="a beautiful landscape",
        name="flux.1.1-pro",
        width=512,
        height=512,
        seed=42,
        api_key="test_api_key",
        validate=True,
    )

    # Check that methods were called
    mock_instance.request.assert_called_once()
    mock_instance.retrieve.assert_called_once()
    mock_instance.save.assert_called_once()
    mock_instance.get_url.assert_called_once()

    # Check result
    assert result["success"] is True
    assert result["prompt"] == "a beautiful landscape"
    assert result["model"] == "flux.1.1-pro"
    assert result["image_path"] == "/path/to/saved/image.png"
    assert result["image_url"] == "https://example.com/image.png"
    assert "Successfully generated" in result["message"]


@pytest.mark.asyncio
async def test_flux_generate_image_no_api_key():
    """Test image generation with no API key."""
    with patch("mcp_toolbox.flux.tools.Config") as mock_config:
        config_instance = MagicMock()
        config_instance.bfl_api_key = None
        mock_config.return_value = config_instance

        result = await flux_generate_image(
            prompt="a beautiful landscape",
            output_dir="/tmp/images",
        )

        assert result["success"] is False
        assert "BFL_API_KEY not provided" in result["error"]


@pytest.mark.asyncio
async def test_flux_generate_image_api_exception(mock_config):
    """Test image generation with API exception."""
    with patch("mcp_toolbox.flux.tools.ImageRequest") as mock_class:
        instance = AsyncMock()
        instance.request = AsyncMock(side_effect=ApiException(400, "Invalid request"))
        mock_class.return_value = instance

        result = await flux_generate_image(
            prompt="a beautiful landscape",
            output_dir="/tmp/images",
        )

        assert result["success"] is False
        assert "API error" in result["error"]


@pytest.mark.asyncio
async def test_flux_generate_image_value_error(mock_config):
    """Test image generation with value error."""
    with patch("mcp_toolbox.flux.tools.ImageRequest") as mock_class:
        instance = AsyncMock()
        instance.request = AsyncMock(side_effect=ValueError("Invalid width"))
        mock_class.return_value = instance

        result = await flux_generate_image(
            prompt="a beautiful landscape",
            output_dir="/tmp/images",
            width=123,  # Not a multiple of 32
        )

        assert result["success"] is False
        assert "Invalid parameters" in result["message"]
