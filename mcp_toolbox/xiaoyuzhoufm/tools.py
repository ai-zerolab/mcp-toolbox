"""XiaoyuZhouFM podcast crawler tools."""

import os
import re
from typing import Annotated, Any

import httpx
from loguru import logger
from pydantic import Field

from mcp_toolbox.app import mcp
from mcp_toolbox.config import Config


class XiaoyuZhouFMCrawler:
    """XiaoyuZhouFM podcast crawler."""

    def __init__(self):
        """Initialize the crawler."""
        self.config = Config()

    async def extract_audio_url(self, url: str) -> str:
        """Extract audio URL from XiaoyuZhouFM episode page.

        Args:
            url: The XiaoyuZhouFM episode URL

        Returns:
            The audio URL

        Raises:
            ValueError: If the audio URL cannot be found
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text

                # Use regex to find the og:audio meta tag
                pattern = r'<meta\s+property="og:audio"\s+content="([^"]+)"'
                match = re.search(pattern, html_content)

                if not match:
                    raise ValueError("Could not find audio URL in the page")

                audio_url = match.group(1)
                return audio_url

            except httpx.HTTPStatusError as e:
                raise ValueError(f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}") from e
            except httpx.RequestError as e:
                raise ValueError(f"Request error: {e}") from e

    async def download_audio(self, audio_url: str, output_path: str) -> str:
        """Download audio file from URL.

        Args:
            audio_url: The audio file URL
            output_path: The path to save the audio file

        Returns:
            The path to the downloaded file

        Raises:
            ValueError: If the download fails
        """
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Downloading audio from {audio_url}")
                response = await client.get(audio_url)
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    f.write(response.content)

                logger.info(f"Audio saved to {output_path}")
                return output_path

            except httpx.HTTPStatusError as e:
                raise ValueError(f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}") from e
            except httpx.RequestError as e:
                raise ValueError(f"Request error: {e}") from e
            except OSError as e:
                raise ValueError(f"IO error: {e}") from e


# Initialize crawler
crawler = XiaoyuZhouFMCrawler()


@mcp.tool(description="Crawl and download a podcast episode from XiaoyuZhouFM.")
async def xiaoyuzhoufm_download(
    xiaoyuzhoufm_url: Annotated[str, Field(description="The URL of the XiaoyuZhouFM episode")],
    output_dir: Annotated[str, Field(description="The directory to save the audio file")],
) -> dict[str, Any]:
    """Crawl and download a podcast episode from XiaoyuZhouFM.

    Args:
        xiaoyuzhoufm_url: The URL of the XiaoyuZhouFM episode
        output_dir: The directory to save the audio file

    Returns:
        A dictionary containing the audio URL and the path to the downloaded file
    """
    try:
        # Validate URL
        if not xiaoyuzhoufm_url.startswith("https://www.xiaoyuzhoufm.com/episode/"):
            raise ValueError("Invalid XiaoyuZhouFM URL. URL should start with 'https://www.xiaoyuzhoufm.com/episode/'")

        # Extract episode ID from URL
        episode_id = xiaoyuzhoufm_url.split("/")[-1]
        if not episode_id:
            episode_id = "episode"

        # Extract audio URL
        audio_url = await crawler.extract_audio_url(xiaoyuzhoufm_url)

        # Determine file extension from audio URL
        file_extension = "m4a"
        if "." in audio_url.split("/")[-1]:
            file_extension = audio_url.split("/")[-1].split(".")[-1]

        # Create output path with episode ID as filename
        output_path = os.path.join(output_dir, f"{episode_id}.{file_extension}")

        # Download audio
        downloaded_path = await crawler.download_audio(audio_url, output_path)

        return {
            "audio_url": audio_url,
            "downloaded_path": downloaded_path,
            "message": f"Successfully downloaded podcast to {downloaded_path}",
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to download podcast: {e!s}",
        }
