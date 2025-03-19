from pathlib import Path
from typing import Any

from markitdown import MarkItDown

from mcp_toolbox.app import mcp

md = MarkItDown(enable_builtins=True, enable_plugins=True)


@mcp.tool(
    description="Convert any file to Markdown, using MarkItDown. Args: input_file (required, The input Markdown file), output_file (required, The output HTML file)",
)
async def convert_file_to_markdown(input_file: str, output_file: str) -> dict[str, Any]:
    """Convert any file to Markdown

    Args:
        input_file: The input Markdown file
        output_file: The output HTML file
    """
    input_file: Path = Path(input_file).expanduser().resolve().absolute()
    output_file: Path = Path(output_file).expanduser().resolve().absolute()

    if not input_file.is_file():
        return {
            "error": f"Input file not found: {input_file.as_posix()}",
            "success": False,
        }

    output_file.parent.mkdir(parents=True, exist_ok=True)

    c = md.convert(input_file.as_posix()).text_content
    output_file.write_text(c)

    return {
        "success": True,
        "input_file": input_file.as_posix(),
        "output_file": output_file.as_posix(),
    }


@mcp.tool(
    description="Convert a URL to Markdown, using MarkItDown. Args: url (required, The URL to convert), output_file (required, The output Markdown file)",
)
async def convert_url_to_markdown(url: str, output_file: str) -> dict[str, Any]:
    """Convert a URL to Markdown

    Args:
        url: The URL to convert
        output_file: The output Markdown file"
    """
    output_file: Path = Path(output_file).expanduser().resolve().absolute()

    output_file.parent.mkdir(parents=True, exist_ok=True)

    c = md.convert_url(url).text_content
    output_file.write_text(c)

    return {
        "success": True,
        "url": url,
        "output_file": output_file.as_posix(),
    }
