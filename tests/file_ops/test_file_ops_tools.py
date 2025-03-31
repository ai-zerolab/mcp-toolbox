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

        # Create files for testing ignore patterns
        temp_file_path = os.path.join(temp_dir, "temp.tmp")
        with open(temp_file_path, "w") as f:
            f.write("Temporary file content")

        node_modules_path = os.path.join(temp_dir, "node_modules")
        os.mkdir(node_modules_path)

        node_module_file_path = os.path.join(node_modules_path, "package.json")
        with open(node_module_file_path, "w") as f:
            f.write('{"name": "test-package"}')

        cache_file_path = os.path.join(temp_dir, "cache.pyc")
        with open(cache_file_path, "w") as f:
            f.write("Python cache file")

        # Test basic directory listing
        result = await list_directory(temp_dir)
        assert result["success"] is True
        assert result["path"] == temp_dir
        assert (
            len(result["entries"]) == 5
        )  # 4 files + 1 directory (node_modules is ignored by default), no hidden files
        assert result["count"] == 5

        # Test with hidden files
        result = await list_directory(temp_dir, include_hidden=True)
        assert result["success"] is True
        assert len(result["entries"]) == 6  # 4 files + 1 directory + 1 hidden file (node_modules is ignored by default)
        assert result["count"] == 6

        # Test recursive listing with explicit empty ignore patterns to see all files
        result = await list_directory(temp_dir, recursive=True, ignore_patterns=[])
        assert result["success"] is True
        assert len(result["entries"]) == 8  # 4 files + 2 directories + 1 subfile + 1 node_module file
        assert result["count"] == 8

        # Test with max depth (with empty ignore patterns to ensure consistent behavior)
        result = await list_directory(temp_dir, recursive=True, max_depth=0, ignore_patterns=[])
        assert result["success"] is True
        assert len(result["entries"]) == 6  # Only top-level entries
        assert result["count"] == 6

        # Test with ignore patterns - single pattern
        result = await list_directory(temp_dir, ignore_patterns=["*.tmp"])
        assert result["success"] is True
        assert len(result["entries"]) == 5  # Excluding temp.tmp
        assert result["count"] == 5
        # Verify temp.tmp is not in the results
        assert not any(entry["name"] == "temp.tmp" for entry in result["entries"])

        # Test with ignore patterns - directory pattern
        result = await list_directory(temp_dir, recursive=True, ignore_patterns=["node_modules"])
        assert result["success"] is True
        assert len(result["entries"]) == 6  # Excluding node_modules directory and its contents
        assert result["count"] == 6
        # Verify node_modules is not in the results
        assert not any(entry["name"] == "node_modules" for entry in result["entries"])

        # Test with multiple ignore patterns
        result = await list_directory(temp_dir, ignore_patterns=["*.tmp", "*.pyc"])
        assert result["success"] is True
        assert len(result["entries"]) == 4  # Excluding temp.tmp and cache.pyc
        assert result["count"] == 4
        # Verify neither temp.tmp nor cache.pyc are in the results
        assert not any(entry["name"] == "temp.tmp" for entry in result["entries"])
        assert not any(entry["name"] == "cache.pyc" for entry in result["entries"])

        # Test default ignore patterns
        # Create directories and files that should be ignored by default
        git_dir_path = os.path.join(temp_dir, ".git")
        os.mkdir(git_dir_path)
        git_file_path = os.path.join(git_dir_path, "config")
        with open(git_file_path, "w") as f:
            f.write("Git config content")

        # Create a .DS_Store file that should be ignored by default
        ds_store_path = os.path.join(temp_dir, ".DS_Store")
        with open(ds_store_path, "w") as f:
            f.write("DS_Store content")

        # Create a node_modules directory that should be ignored by default
        node_modules_dir = os.path.join(temp_dir, "node_modules")
        os.makedirs(node_modules_dir, exist_ok=True)
        node_modules_file = os.path.join(node_modules_dir, "package.json")
        with open(node_modules_file, "w") as f:
            f.write('{"name": "test-package"}')

        # Test with explicit ignore patterns that match the default ones
        result = await list_directory(
            temp_dir, recursive=True, include_hidden=True, ignore_patterns=[".git", ".DS_Store", "node_modules"]
        )
        assert result["success"] is True
        # Should not include .git directory or .DS_Store file due to specified ignore patterns
        assert not any(entry["name"] == ".git" for entry in result["entries"])
        assert not any(entry["name"] == ".DS_Store" for entry in result["entries"])
        assert not any(entry["name"] == "node_modules" for entry in result["entries"])
        assert any(entry["name"] == ".hidden_file" for entry in result["entries"])  # Should include other hidden files

        # Test with explicit None for ignore_patterns (should use defaults)
        result = await list_directory(temp_dir, recursive=True, include_hidden=True, ignore_patterns=None)
        assert result["success"] is True
        # Should not include node_modules directory due to default ignore patterns
        assert not any(entry["name"] == "node_modules" for entry in result["entries"])
        # Should not include .git directory due to default ignore patterns
        assert not any(entry["name"] == ".git" for entry in result["entries"])
        # Should not include .DS_Store file due to default ignore patterns
        assert not any(entry["name"] == ".DS_Store" for entry in result["entries"])

        # Test with empty list for ignore_patterns (should override defaults)
        result = await list_directory(temp_dir, recursive=True, include_hidden=True, ignore_patterns=[])
        assert result["success"] is True
        # Should include .git directory and .DS_Store file since we're overriding defaults with empty list
        assert any(entry["name"] == ".git" for entry in result["entries"])
        assert any(entry["name"] == ".DS_Store" for entry in result["entries"])

        # Test combining ignore patterns with other parameters
        result = await list_directory(
            temp_dir,
            recursive=True,
            include_hidden=True,
            ignore_patterns=["node_modules", "*.tmp", "*.pyc", ".git", ".DS_Store"],
        )
        assert result["success"] is True
        # Should include only .hidden_file, file1.txt, file2.txt, subdir, and subfile.txt
        assert len(result["entries"]) == 5
        assert result["count"] == 5
        # Verify specific files are included/excluded
        assert any(entry["name"] == ".hidden_file" for entry in result["entries"])
        assert any(entry["name"] == "file1.txt" for entry in result["entries"])
        assert any(entry["name"] == "file2.txt" for entry in result["entries"])
        assert any(entry["name"] == "subdir" for entry in result["entries"])
        assert any(entry["name"] == "subfile.txt" for entry in result["entries"])
        # Verify excluded files
        assert not any(entry["name"] == "node_modules" for entry in result["entries"])
        assert not any(entry["name"] == "temp.tmp" for entry in result["entries"])
        assert not any(entry["name"] == "cache.pyc" for entry in result["entries"])
        assert not any(entry["name"] == ".git" for entry in result["entries"])
        assert not any(entry["name"] == ".DS_Store" for entry in result["entries"])

        # Test non-existent directory
        result = await list_directory("/non/existent/dir")
        assert result["success"] is False
        assert "Directory not found" in result["error"]

        # Test file path instead of directory
        result = await list_directory(file1_path)
        assert result["success"] is False
        assert "Path is not a directory" in result["error"]

        # Test directory with tilde in path (with empty ignore patterns to ensure consistent behavior)
        with patch("pathlib.Path.expanduser", return_value=Path(temp_dir)) as mock_expanduser:
            result = await list_directory("~/test_dir", ignore_patterns=[])
            assert result["success"] is True
            assert len(result["entries"]) == 6  # 4 files + 2 directories, no hidden files
            assert result["count"] == 6
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
