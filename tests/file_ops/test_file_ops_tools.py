"""Tests for file operations tools."""

import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_toolbox.file_ops.tools import (
    _format_mode,
    _get_file_info,
    list_directory,
    read_file_content,
    replace_in_file,
    write_file_content,
)


@pytest.mark.asyncio
async def test_read_file_content():
    """Test reading file content."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write("Test content")
        temp_path = temp_file.name

    try:
        # Test reading the entire file
        result = await read_file_content(temp_path)
        assert result["success"] is True
        assert result["content"] == "Test content"
        assert "size" in result
        assert "last_modified" in result
        assert result["total_chunks"] == 1
        assert result["chunk_index"] == 0
        assert result["is_last_chunk"] is True

        # Test reading a non-existent file
        result = await read_file_content("/non/existent/file")
        assert result["success"] is False
        assert "File not found" in result["error"]

        # Test reading a directory
        temp_dir = tempfile.mkdtemp()
        try:
            result = await read_file_content(temp_dir)
            assert result["success"] is False
            assert "Path is not a file" in result["error"]
        finally:
            os.rmdir(temp_dir)

        # Test reading a file with tilde in path
        with patch("pathlib.Path.expanduser", return_value=Path(temp_path)) as mock_expanduser:
            result = await read_file_content("~/test_file.txt")
            assert result["success"] is True
            assert result["content"] == "Test content"
            mock_expanduser.assert_called_once()

        # Test reading with custom chunk size
        result = await read_file_content(temp_path, chunk_size=5)
        assert result["success"] is True
        assert result["content"] == "Test "
        assert result["chunk_size"] == 5
        assert result["chunk_index"] == 0
        assert result["total_chunks"] == 3  # "Test content" is 12 chars, so 3 chunks of 5 bytes
        assert result["is_last_chunk"] is False

        # Test reading second chunk
        result = await read_file_content(temp_path, chunk_size=5, chunk_index=1)
        assert result["success"] is True
        assert result["content"] == "conte"
        assert result["chunk_index"] == 1
        assert result["is_last_chunk"] is False

        # Test reading last chunk
        result = await read_file_content(temp_path, chunk_size=5, chunk_index=2)
        assert result["success"] is True
        assert result["content"] == "nt"
        assert result["chunk_index"] == 2
        assert result["is_last_chunk"] is True
        assert result["chunk_actual_size"] == 2  # Only 2 bytes in the last chunk

        # Test reading with invalid chunk index
        result = await read_file_content(temp_path, chunk_size=5, chunk_index=3)
        assert result["success"] is False
        assert "Invalid chunk index" in result["error"]

    finally:
        # Clean up
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_write_file_content():
    """Test writing file content."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test writing to a new file
        file_path = os.path.join(temp_dir, "test_file.txt")
        result = await write_file_content(file_path, "Test content")
        assert result["success"] is True
        assert os.path.exists(file_path)
        with open(file_path) as f:
            assert f.read() == "Test content"

        # Test appending to a file
        result = await write_file_content(file_path, " appended", append=True)
        assert result["success"] is True
        with open(file_path) as f:
            assert f.read() == "Test content appended"

        # Test writing to a nested path
        nested_path = os.path.join(temp_dir, "nested", "dir", "test_file.txt")
        result = await write_file_content(nested_path, "Nested content")
        assert result["success"] is True
        assert os.path.exists(nested_path)
        with open(nested_path) as f:
            assert f.read() == "Nested content"

        # Test writing to a file with tilde in path
        tilde_path = "~/test_file_tilde.txt"
        expanded_path = os.path.join(temp_dir, "test_file_tilde.txt")

        with patch("pathlib.Path.expanduser", return_value=Path(expanded_path)) as mock_expanduser:
            result = await write_file_content(tilde_path, "Tilde content")
            assert result["success"] is True
            mock_expanduser.assert_called_once()
            # Verify the file was created at the expanded path
            assert os.path.exists(expanded_path)
            with open(expanded_path) as f:
                assert f.read() == "Tilde content"


@pytest.mark.asyncio
async def test_replace_in_file():
    """Test replacing content in a file."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write("Hello world! This is a test.")
        temp_path = temp_file.name

    try:
        # Test replacing content
        result = await replace_in_file(temp_path, r"world", "universe")
        assert result["success"] is True
        assert result["replacements"] == 1
        with open(temp_path) as f:
            assert f.read() == "Hello universe! This is a test."

        # Test replacing with count
        result = await replace_in_file(temp_path, r"[aeiou]", "X", count=2)
        assert result["success"] is True
        assert result["replacements"] == 2
        with open(temp_path) as f:
            assert f.read() == "HXllX universe! This is a test."

        # Test replacing with invalid regex
        result = await replace_in_file(temp_path, r"[unclosed", "X")
        assert result["success"] is False
        assert "Invalid regular expression" in result["error"]

        # Test replacing in non-existent file
        result = await replace_in_file("/non/existent/file", r"test", "replacement")
        assert result["success"] is False
        assert "File not found" in result["error"]

        # Test replacing in a file with tilde in path
        with patch("pathlib.Path.expanduser", return_value=Path(temp_path)) as mock_expanduser:
            result = await replace_in_file("~/test_file.txt", r"HXllX", "Hello")
            assert result["success"] is True
            assert result["replacements"] == 1
            mock_expanduser.assert_called_once()
            with open(temp_path) as f:
                assert f.read() == "Hello universe! This is a test."

    finally:
        # Clean up
        os.unlink(temp_path)


def test_format_mode():
    """Test formatting file mode."""
    # Directory with full permissions
    dir_mode = stat.S_IFDIR | 0o777
    assert _format_mode(dir_mode) == "drwxrwxrwx"

    # Regular file with read-only permissions
    file_mode = stat.S_IFREG | 0o444
    assert _format_mode(file_mode) == "-r--r--r--"

    # Executable file with owner-only permissions
    exec_mode = stat.S_IFREG | 0o700
    assert _format_mode(exec_mode) == "-rwx------"

    # Symlink with mixed permissions
    link_mode = stat.S_IFLNK | 0o751
    assert _format_mode(link_mode) == "lrwxr-x--x"


@pytest.mark.asyncio
async def test_list_directory():
    """Test listing directory contents."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some files and subdirectories
        file1_path = os.path.join(temp_dir, "file1.txt")
        with open(file1_path, "w") as f:
            f.write("File 1 content")

        file2_path = os.path.join(temp_dir, "file2.txt")
        with open(file2_path, "w") as f:
            f.write("File 2 content")

        hidden_file_path = os.path.join(temp_dir, ".hidden_file")
        with open(hidden_file_path, "w") as f:
            f.write("Hidden file content")

        subdir_path = os.path.join(temp_dir, "subdir")
        os.mkdir(subdir_path)

        subfile_path = os.path.join(subdir_path, "subfile.txt")
        with open(subfile_path, "w") as f:
            f.write("Subfile content")

        # Test basic directory listing
        result = await list_directory(temp_dir)
        assert result["success"] is True
        assert result["path"] == temp_dir
        assert len(result["entries"]) == 3  # 2 files + 1 directory, no hidden files
        assert result["count"] == 3

        # Test with hidden files
        result = await list_directory(temp_dir, include_hidden=True)
        assert result["success"] is True
        assert len(result["entries"]) == 4  # 3 files + 1 directory, including hidden file
        assert result["count"] == 4

        # Test recursive listing
        result = await list_directory(temp_dir, recursive=True)
        assert result["success"] is True
        assert len(result["entries"]) == 4  # 2 files + 1 directory + 1 subfile
        assert result["count"] == 4

        # Test with max depth
        result = await list_directory(temp_dir, recursive=True, max_depth=0)
        assert result["success"] is True
        assert len(result["entries"]) == 3  # Only top-level entries
        assert result["count"] == 3

        # Test non-existent directory
        result = await list_directory("/non/existent/dir")
        assert result["success"] is False
        assert "Directory not found" in result["error"]

        # Test file path instead of directory
        result = await list_directory(file1_path)
        assert result["success"] is False
        assert "Path is not a directory" in result["error"]

        # Test directory with tilde in path
        with patch("pathlib.Path.expanduser", return_value=Path(temp_dir)) as mock_expanduser:
            result = await list_directory("~/test_dir")
            assert result["success"] is True
            assert len(result["entries"]) == 3  # 2 files + 1 directory, no hidden files
            assert result["count"] == 3
            mock_expanduser.assert_called_once()


def test_get_file_info():
    """Test getting file information."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write("Test content")
        temp_path = temp_file.name

    try:
        # Get file info
        file_path = Path(temp_path)
        file_info = _get_file_info(file_path)

        # Check basic properties
        assert file_info["name"] == file_path.name
        assert file_info["path"] == str(file_path)
        assert file_info["type"] == "file"
        assert file_info["size"] == len("Test content")
        assert "size_formatted" in file_info
        assert "permissions" in file_info
        assert "mode" in file_info
        assert "owner" in file_info
        assert "group" in file_info
        assert "created" in file_info
        assert "modified" in file_info
        assert "accessed" in file_info

    finally:
        # Clean up
        os.unlink(temp_path)
