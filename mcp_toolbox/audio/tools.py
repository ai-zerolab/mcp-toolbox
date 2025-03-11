"""Audio processing tools for transcription and analysis."""

import datetime
import os
from pathlib import Path
from typing import Any

import whisper
from loguru import logger

from mcp_toolbox.app import mcp

# Global variables to cache model and audio data
_model = None
_model_name = None
_audio = None
_audio_path = None
_detected_language = None


def load_model(model_name="base"):
    """
    Load and cache the Whisper model.

    Args:
        model_name: The name of the Whisper model to load (tiny, base, small, medium, large)

    Returns:
        The loaded Whisper model
    """
    global _model, _model_name

    # Load model if not loaded or if model name has changed
    if _model is None or _model_name != model_name:
        logger.info(f"Loading Whisper model: {model_name}")
        _model = whisper.load_model(model_name)
        _model_name = model_name

    return _model


def load_audio(audio_path, model_name="base"):
    """
    Load and cache the audio file.

    Args:
        audio_path: The path to the audio file
        model_name: The name of the Whisper model to use for language detection

    Returns:
        The loaded audio data
    """
    global _audio, _audio_path, _detected_language, _model

    # Ensure model is loaded
    model = load_model(model_name)

    # Only reload if it's a different file or not loaded yet
    audio_path = Path(audio_path).expanduser().resolve().absolute().as_posix()
    if _audio is None or _audio_path != audio_path:
        logger.info(f"Loading audio: {audio_path}")
        _audio = whisper.load_audio(audio_path)
        _audio_path = audio_path

        # Get audio duration in seconds
        audio_duration = len(_audio) / 16000  # Whisper uses 16kHz audio
        logger.info(f"Audio duration: {datetime.timedelta(seconds=int(audio_duration))!s}")

        # Detect language from the first chunk
        chunk_samples = int(30 * 16000)  # Use 30 seconds for language detection
        first_chunk = whisper.pad_or_trim(_audio[:chunk_samples])
        mel = whisper.log_mel_spectrogram(first_chunk).to(model.device)
        _, probs = model.detect_language(mel)
        _detected_language = max(probs, key=probs.get)
        logger.info(f"Detected language: {_detected_language}")

    return _audio


@mcp.tool(
    description="Get the length of an audio file in seconds. Args: audio_path (required, The path to the audio file)"
)
async def get_audio_length(audio_path: str) -> dict[str, Any]:
    """Get the length of an audio file in seconds.

    Args:
        audio_path: The path to the audio file

    Returns:
        A dictionary containing the audio length in seconds and formatted time
    """
    try:
        if not os.path.exists(audio_path):
            raise ValueError(f"Audio file not found: {audio_path}")

        # Load audio
        audio = whisper.load_audio(audio_path)

        # Calculate duration
        audio_duration_seconds = len(audio) / 16000  # Whisper uses 16kHz audio
        formatted_duration = str(datetime.timedelta(seconds=int(audio_duration_seconds)))

        return {
            "duration_seconds": audio_duration_seconds,
            "formatted_duration": formatted_duration,
            "message": f"Audio length: {formatted_duration} ({audio_duration_seconds:.2f} seconds)",
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to get audio length: {e!s}",
        }


@mcp.tool(
    description="Get transcribed text from a specific time range in an audio file. Args: audio_path (required, The path to the audio file), start_time (required, Start time in seconds), end_time (required, End time in seconds), model_name (optional, Whisper model name: tiny, base, small, medium, large)"
)
async def get_audio_text(
    audio_path: str, start_time: float, end_time: float, model_name: str = "base"
) -> dict[str, Any]:
    """Extract and transcribe text from a specific time range in an audio file.

    Args:
        audio_path: The path to the audio file
        start_time: Start time in seconds
        end_time: End time in seconds
        model_name: Whisper model name (tiny, base, small, medium, large)
        initial_prompt: Initial prompt to guide transcription

    Returns:
        A dictionary containing the transcribed text and time range
    """
    try:
        if not os.path.exists(audio_path):
            raise ValueError(f"Audio file not found: {audio_path}")

        # Load audio to detect language if not already loaded
        _ = load_audio(audio_path, model_name)
        if _detected_language == "zh":
            initial_prompt = "以下是普通话的句子"
        elif _detected_language == "en":
            initial_prompt = "The following is English speech"
        else:
            initial_prompt = ""

        # Load model and audio (uses cached versions if already loaded)
        model = load_model(model_name)
        audio = load_audio(audio_path, model_name)

        # Convert times to sample indices
        sample_rate = 16000  # Whisper uses 16kHz audio
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)

        # Ensure indices are within bounds
        audio_length = len(audio)
        start_sample = max(0, min(start_sample, audio_length - 1))
        end_sample = max(start_sample, min(end_sample, audio_length))

        # Extract the requested audio segment
        segment = audio[start_sample:end_sample]

        # If segment is too short, pad it
        if len(segment) < 0.5 * sample_rate:  # Less than 0.5 seconds
            logger.warning("Audio segment is very short, results may be poor")
            segment = whisper.pad_or_trim(segment, 0.5 * sample_rate)

        # Transcribe the segment
        result = model.transcribe(
            segment,
            language=_detected_language,
            initial_prompt=initial_prompt,
            verbose=False,
        )

        # Format time range for display
        start_formatted = str(datetime.timedelta(seconds=int(start_time)))
        end_formatted = str(datetime.timedelta(seconds=int(end_time)))

        # Extract and return the text
        transcribed_text = result["text"].strip()

        return {
            "text": transcribed_text,
            "start_time": start_time,
            "end_time": end_time,
            "time_range": f"{start_formatted} - {end_formatted}",
            "language": _detected_language,
            "message": "Successfully transcribed audio",
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to transcribe audio: {e!s}",
        }
