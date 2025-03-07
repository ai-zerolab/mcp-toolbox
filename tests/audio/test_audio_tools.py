"""Tests for audio tools."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_toolbox.audio.tools import get_audio_length, get_audio_text


@pytest.fixture
def mock_whisper():
    """Mock whisper module."""
    with patch("mcp_toolbox.audio.tools.whisper") as mock_whisper:
        # Mock load_audio to return a numpy array of a specific length
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 16000 * 60  # 60 seconds of audio at 16kHz
        mock_whisper.load_audio.return_value = mock_audio

        # Mock the model
        mock_model = MagicMock()
        mock_model.detect_language.return_value = (None, {"en": 0.9, "zh": 0.1})
        mock_model.transcribe.return_value = {"text": "Successfully transcribed audio"}
        mock_whisper.load_model.return_value = mock_model

        yield mock_whisper


@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists to return True."""
    with patch("os.path.exists", return_value=True):
        yield


@pytest.mark.asyncio
async def test_get_audio_length(mock_whisper, mock_os_path_exists):
    """Test get_audio_length function."""
    result = await get_audio_length("test.m4a")

    # Check that the function returns the expected values
    assert "duration_seconds" in result
    assert "formatted_duration" in result
    assert "message" in result
    assert result["duration_seconds"] == 60.0
    assert result["formatted_duration"] == "0:01:00"
    assert "60.00 seconds" in result["message"]

    # Check that whisper.load_audio was called with the correct arguments
    mock_whisper.load_audio.assert_called_once_with("test.m4a")


@pytest.mark.asyncio
async def test_get_audio_length_file_not_found():
    """Test get_audio_length function with a non-existent file."""
    with patch("os.path.exists", return_value=False):
        result = await get_audio_length("nonexistent.m4a")

    # Check that the function returns an error
    assert "error" in result
    assert "message" in result
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_get_audio_text(mock_whisper, mock_os_path_exists):
    """Test get_audio_text function."""
    # Set up global variables in the module
    with patch("mcp_toolbox.audio.tools._detected_language", "en"):
        result = await get_audio_text("test.m4a", 10.0, 20.0, "base")

    # Check that the function returns the expected values
    assert "text" in result
    assert "start_time" in result
    assert "end_time" in result
    assert "time_range" in result
    assert "language" in result
    assert "message" in result
    assert result["text"] == "Successfully transcribed audio"
    assert result["start_time"] == 10.0
    assert result["end_time"] == 20.0
    assert result["time_range"] == "0:00:10 - 0:00:20"
    assert "Successfully transcribed audio" in result["message"]

    # Check that whisper.load_model and transcribe were called
    mock_whisper.load_model.assert_called()
    mock_whisper.load_model().transcribe.assert_called()


@pytest.mark.asyncio
async def test_get_audio_text_file_not_found():
    """Test get_audio_text function with a non-existent file."""
    with patch("os.path.exists", return_value=False):
        result = await get_audio_text("nonexistent.m4a", 10.0, 20.0)

    # Check that the function returns an error
    assert "error" in result
    assert "message" in result
    assert "not found" in result["error"]
