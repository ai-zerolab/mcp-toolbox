"""File operations tools for MCP-Toolbox."""

import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field

from mcp_toolbox.app import mcp


@mcp.tool(description="Read file content.")
async def read_file_content(
    path: Annotated[str, Field(description="Path to the file to read")],
    encoding: Annotated[str, Field(default="utf-8", description="File encoding")] = "utf-8",
    chunk_size: Annotated[
        int, Field(default=1000000, description="Size of each chunk in bytes, default: 1MB")
    ] = 1000000,
    chunk_index: Annotated[int, Field(default=0, description="Index of the chunk to retrieve, 0-based")] = 0,
) -> dict[str, Any]:
    """Read content from a file, with support for chunked reading for large files.

    Args:
        path: Path to the file to read
        encoding: Optional. File encoding (default: utf-8)
        chunk_size: Optional. Size of each chunk in bytes (default: 1000000, which about 1MB)
        chunk_index: Optional. Index of the chunk to retrieve, 0-based (default: 0)

    Returns:
        Dictionary containing content and metadata, including chunking information
    """
    try:
        file_path = Path(path).expanduser()

        if not file_path.exists():
            return {
                "error": f"File not found: {path}",
                "content": "",
                "success": False,
            }

        if not file_path.is_file():
            return {
                "error": f"Path is not a file: {path}",
                "content": "",
                "success": False,
            }

        # Get file stats
        stats = file_path.stat()
        file_size = stats.st_size

        # Calculate total chunks
        total_chunks = (file_size + chunk_size - 1) // chunk_size  # Ceiling division

        # Validate chunk_index
        if chunk_index < 0 or (file_size > 0 and chunk_index >= total_chunks):
            return {
                "error": f"Invalid chunk index: {chunk_index}. Valid range is 0 to {total_chunks - 1}",
                "content": "",
                "success": False,
                "total_chunks": total_chunks,
                "file_size": file_size,
            }

        # Calculate start and end positions for the chunk
        start_pos = chunk_index * chunk_size
        end_pos = min(start_pos + chunk_size, file_size)
        chunk_actual_size = end_pos - start_pos

        # Read the specified chunk
        content = ""
        with open(file_path, "rb") as f:
            f.seek(start_pos)
            chunk_bytes = f.read(chunk_actual_size)

            try:
                # Try to decode as text
                content = chunk_bytes.decode(encoding, errors="replace")
            except UnicodeDecodeError:
                # If decoding fails, return base64 encoded binary data
                import base64

                content = base64.b64encode(chunk_bytes).decode("ascii")
                encoding = f"base64 (original: {encoding})"

        return {
            "content": content,
            "size": file_size,
            "chunk_size": chunk_size,
            "chunk_index": chunk_index,
            "chunk_actual_size": chunk_actual_size,
            "total_chunks": total_chunks,
            "is_last_chunk": chunk_index == total_chunks - 1,
            "encoding": encoding,
            "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "success": True,
        }
    except UnicodeDecodeError:
        return {
            "error": f"Failed to decode file with encoding {encoding}. Try a different encoding.",
            "content": "",
            "success": False,
        }
    except Exception as e:
        return {
            "error": f"Failed to read file: {e!s}",
            "content": "",
            "success": False,
        }


@mcp.tool(description="Write content to a file.")
async def write_file_content(
    path: Annotated[str, Field(description="Path to the file to write")],
    content: Annotated[str, Field(description="Content to write")],
    encoding: Annotated[str, Field(default="utf-8", description="File encoding")] = "utf-8",
    append: Annotated[bool, Field(default=False, description="Whether to append to the file")] = False,
) -> dict[str, Any]:
    """Write content to a file.

    Args:
        path: Path to the file to write
        content: Content to write to the file
        encoding: Optional. File encoding (default: utf-8)
        append: Optional. Whether to append to the file (default: False)

    Returns:
        Dictionary containing success status and metadata
    """
    try:
        file_path = Path(path).expanduser()

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        mode = "a" if append else "w"
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)

        # Get file stats
        stats = file_path.stat()

        return {
            "path": str(file_path),
            "size": stats.st_size,
            "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "success": True,
        }
    except Exception as e:
        return {
            "error": f"Failed to write file: {e!s}",
            "path": path,
            "success": False,
        }


@mcp.tool(description="Replace content in a file using regular expressions.")
async def replace_in_file(
    path: Annotated[str, Field(description="Path to the file")],
    pattern: Annotated[str, Field(description="Regular expression pattern")],
    replacement: Annotated[str, Field(description="Replacement string")],
    encoding: Annotated[str, Field(default="utf-8", description="File encoding")] = "utf-8",
    count: Annotated[int, Field(default=0, description="Maximum number of replacements")] = 0,
) -> dict[str, Any]:
    """Replace content in a file using regular expressions.

    Args:
        path: Path to the file
        pattern: Regular expression pattern
        replacement: Replacement string
        encoding: Optional. File encoding (default: utf-8)
        count: Optional. Maximum number of replacements (default: 0, which means all occurrences)

    Returns:
        Dictionary containing success status and replacement information
    """
    try:
        file_path = Path(path).expanduser()

        if not file_path.exists():
            return {
                "error": f"File not found: {path}",
                "success": False,
                "replacements": 0,
            }

        if not file_path.is_file():
            return {
                "error": f"Path is not a file: {path}",
                "success": False,
                "replacements": 0,
            }

        # Read file content
        with open(file_path, encoding=encoding) as f:
            content = f.read()

        # Compile regex pattern
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return {
                "error": f"Invalid regular expression: {e!s}",
                "success": False,
                "replacements": 0,
            }

        # Replace content
        new_content, replacements = regex.subn(replacement, content, count=count)

        if replacements > 0:
            # Write updated content back to file
            with open(file_path, "w", encoding=encoding) as f:
                f.write(new_content)

        return {
            "path": str(file_path),
            "replacements": replacements,
            "success": True,
        }
    except UnicodeDecodeError:
        return {
            "error": f"Failed to decode file with encoding {encoding}. Try a different encoding.",
            "success": False,
            "replacements": 0,
        }
    except Exception as e:
        return {
            "error": f"Failed to replace content: {e!s}",
            "success": False,
            "replacements": 0,
        }


def _format_mode(mode: int) -> str:
    """Format file mode into a string representation.

    Args:
        mode: File mode as an integer

    Returns:
        String representation of file permissions
    """
    result = ""

    # File type
    if stat.S_ISDIR(mode):
        result += "d"
    elif stat.S_ISLNK(mode):
        result += "l"
    else:
        result += "-"

    # User permissions
    result += "r" if mode & stat.S_IRUSR else "-"
    result += "w" if mode & stat.S_IWUSR else "-"
    result += "x" if mode & stat.S_IXUSR else "-"

    # Group permissions
    result += "r" if mode & stat.S_IRGRP else "-"
    result += "w" if mode & stat.S_IWGRP else "-"
    result += "x" if mode & stat.S_IXGRP else "-"

    # Other permissions
    result += "r" if mode & stat.S_IROTH else "-"
    result += "w" if mode & stat.S_IWOTH else "-"
    result += "x" if mode & stat.S_IXOTH else "-"

    return result


def _get_file_info(path: Path) -> dict[str, Any]:
    """Get detailed information about a file or directory.

    Args:
        path: Path to the file or directory

    Returns:
        Dictionary containing file information
    """
    stats = path.stat()

    # Format timestamps
    mtime = datetime.fromtimestamp(stats.st_mtime).isoformat()
    ctime = datetime.fromtimestamp(stats.st_ctime).isoformat()
    atime = datetime.fromtimestamp(stats.st_atime).isoformat()

    # Get file type
    if path.is_dir():
        file_type = "directory"
    elif path.is_symlink():
        file_type = "symlink"
    else:
        file_type = "file"

    # Format size
    size = stats.st_size
    size_str = f"{size} bytes"
    if size >= 1024:
        size_str = f"{size / 1024:.2f} KB"
    if size >= 1024 * 1024:
        size_str = f"{size / (1024 * 1024):.2f} MB"
    if size >= 1024 * 1024 * 1024:
        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"

    return {
        "name": path.name,
        "path": str(path),
        "type": file_type,
        "size": size,
        "size_formatted": size_str,
        "permissions": _format_mode(stats.st_mode),
        "mode": stats.st_mode,
        "owner": stats.st_uid,
        "group": stats.st_gid,
        "created": ctime,
        "modified": mtime,
        "accessed": atime,
    }


@mcp.tool(description="List directory contents with detailed information.")
async def list_directory(
    path: Annotated[str, Field(description="Directory path")],
    recursive: Annotated[bool, Field(default=False, description="Whether to list recursively")] = False,
    max_depth: Annotated[int, Field(default=-1, description="Maximum recursion depth")] = -1,
    include_hidden: Annotated[bool, Field(default=False, description="Whether to include hidden files")] = False,
) -> dict[str, Any]:
    """List directory contents with detailed information.

    Args:
        path: Directory path
        recursive: Optional. Whether to list recursively (default: False)
        max_depth: Optional. Maximum recursion depth (default: -1, which means no limit)
        include_hidden: Optional. Whether to include hidden files (default: False)

    Returns:
        Dictionary containing directory contents and metadata
    """
    try:
        dir_path = Path(path).expanduser()

        if not dir_path.exists():
            return {
                "error": f"Directory not found: {path}",
                "entries": [],
                "success": False,
            }

        if not dir_path.is_dir():
            return {
                "error": f"Path is not a directory: {path}",
                "entries": [],
                "success": False,
            }

        entries = []

        def process_directory(current_path: Path, current_depth: int = 0) -> None:
            """Process a directory and its contents recursively.

            Args:
                current_path: Path to the current directory
                current_depth: Current recursion depth
            """
            nonlocal entries

            # Check if we've reached the maximum depth
            if max_depth >= 0 and current_depth > max_depth:
                return

            try:
                # List directory contents
                for item in current_path.iterdir():
                    # Skip hidden files if not included
                    if not include_hidden and item.name.startswith("."):
                        continue

                    # Get file information
                    file_info = _get_file_info(item)
                    file_info["depth"] = current_depth
                    entries.append(file_info)

                    # Recursively process subdirectories
                    if recursive and item.is_dir():
                        process_directory(item, current_depth + 1)
            except PermissionError:
                # Add an entry indicating permission denied
                entries.append({
                    "name": current_path.name,
                    "path": str(current_path),
                    "type": "directory",
                    "error": "Permission denied",
                    "depth": current_depth,
                })

        # Start processing from the root directory
        process_directory(dir_path)

        return {
            "path": str(dir_path),
            "entries": entries,
            "count": len(entries),
            "success": True,
        }
    except Exception as e:
        return {
            "error": f"Failed to list directory: {e!s}",
            "entries": [],
            "success": False,
        }
