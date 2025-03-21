"""Flux API image generation tools."""

from pathlib import Path
from typing import Annotated, Any

from loguru import logger
from pydantic import Field

from mcp_toolbox.app import mcp
from mcp_toolbox.config import Config
from mcp_toolbox.flux.api import ApiException, ImageRequest


@mcp.tool(description="Generate an image using the Flux API and save it to a local file.")
async def flux_generate_image(
    prompt: Annotated[str, Field(description="The text prompt for image generation")],
    output_dir: Annotated[str, Field(description="The directory to save the image")],
    model_name: Annotated[str, Field(default="flux.1.1-pro", description="The model version to use")] = "flux.1.1-pro",
    width: Annotated[int | None, Field(default=None, description="Width of the image in pixels")] = None,
    height: Annotated[int | None, Field(default=None, description="Height of the image in pixels")] = None,
    seed: Annotated[int | None, Field(default=None, description="Seed for reproducibility")] = None,
) -> dict[str, Any]:
    """Generate an image using the Flux API and save it to a local file.

    Args:
        prompt: The text prompt for image generation
        output_dir: The directory to save the image
        model_name: The model version to use (default: flux.1.1-pro)
        width: Width of the image in pixels (must be a multiple of 32, between 256 and 1440)
        height: Height of the image in pixels (must be a multiple of 32, between 256 and 1440)
        seed: Optional seed for reproducibility

    Returns:
        A dictionary containing information about the generated image
    """
    config = Config()

    if not config.bfl_api_key:
        return {
            "success": False,
            "error": "BFL_API_KEY not provided. Set BFL_API_KEY environment variable.",
        }

    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate a filename based on the prompt
        filename = "_".join(prompt.split()[:5]).lower()
        filename = "".join(c if c.isalnum() or c == "_" else "_" for c in filename)
        if len(filename) > 50:
            filename = filename[:50]

        # Full path for the image (extension will be added by the save method)
        image_path = output_path / filename

        logger.info(f"Generating image with prompt: {prompt}")

        # Create image request
        image_request = ImageRequest(
            prompt=prompt,
            name=model_name,
            width=width,
            height=height,
            seed=seed,
            api_key=config.bfl_api_key,
            validate=True,
        )

        # Request and save the image
        logger.info("Requesting image from Flux API...")
        await image_request.request()

        logger.info("Waiting for image generation to complete...")
        await image_request.retrieve()

        logger.info("Saving image to disk...")
        saved_path = await image_request.save(str(image_path))

        # Get the image URL
        image_url = await image_request.get_url()

        return {
            "success": True,
            "prompt": prompt,
            "model": model_name,
            "image_path": saved_path,
            "image_url": image_url,
            "message": f"Successfully generated and saved image to {saved_path}",
        }

    except ApiException as e:
        return {
            "success": False,
            "error": f"API error: {e}",
            "message": f"Failed to generate image: {e}",
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Invalid parameters: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate image: {e}",
        }
