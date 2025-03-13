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

    original_text = input_file.read_text()
    c = md.convert(original_text).text_content
    output_file.write_text(c)

    return {
        "success": True,
        "input_file": input_file.as_posix(),
        "output_file": output_file.as_posix(),
    }


@mcp.tool(
    description="Convert text to Markdown, using MarkItDown. Args: text (required, The text to convert)",
)
async def convert_str_to_markdown(text: str) -> str:
    return md.convert(text).text_content
