import json
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_toolbox.figma.tools import (
    CacheManager,
    FigmaApiClient,
    figma_delete_comment,
    figma_get_comments,
    figma_get_component,
    figma_get_file,
    figma_get_file_components,
    figma_get_file_nodes,
    figma_get_file_styles,
    figma_get_image,
    figma_get_image_fills,
    figma_get_project_files,
    figma_get_style,
    figma_get_team_component_sets,
    figma_get_team_components,
    figma_get_team_projects,
    figma_get_team_styles,
    figma_post_comment,
)


# Helper function to load mock data
def load_mock_data(filename):
    mock_dir = Path(__file__).parent.parent / "mock" / "figma"
    file_path = mock_dir / filename

    if not file_path.exists():
        # Create empty mock data if it doesn't exist
        mock_data = {"mock": "data"}
        with open(file_path, "w") as f:
            json.dump(mock_data, f)

    with open(file_path) as f:
        return json.load(f)


# Patch the FigmaApiClient.make_request method
@pytest.fixture
def mock_make_request():
    with patch.object(FigmaApiClient, "make_request") as mock:

        def side_effect(path, method="GET", data=None):
            # Extract the tool name from the path
            parts = path.strip("/").split("/")

            if len(parts) >= 2 and parts[0] == "files" and parts[1]:
                file_key = parts[1]

                if len(parts) == 2:
                    # get_file
                    return load_mock_data("get_file.json")
                elif len(parts) == 3:
                    if parts[2] == "nodes":
                        # get_file_nodes
                        return load_mock_data("get_file_nodes.json")
                    elif parts[2] == "images":
                        # get_image_fills
                        return load_mock_data("get_image_fills.json")
                    elif parts[2] == "components":
                        # get_file_components
                        return load_mock_data("get_file_components.json")
                    elif parts[2] == "styles":
                        # get_file_styles
                        return load_mock_data("get_file_styles.json")
                    elif parts[2] == "comments":
                        if method == "GET":
                            # get_comments
                            return load_mock_data("get_comments.json")
                        elif method == "POST":
                            # post_comment
                            return load_mock_data("post_comment.json")
                elif len(parts) == 4 and parts[2] == "comments":
                    # delete_comment
                    return load_mock_data("delete_comment.json")

            elif parts[0] == "images" and len(parts) >= 2:
                # get_image
                return load_mock_data("get_image.json")

            elif parts[0] == "teams" and len(parts) >= 3:
                team_id = parts[1]

                if parts[2] == "projects":
                    # get_team_projects
                    return load_mock_data("get_team_projects.json")
                elif parts[2] == "components":
                    # get_team_components
                    return load_mock_data("get_team_components.json")
                elif parts[2] == "component_sets":
                    # get_team_component_sets
                    return load_mock_data("get_team_component_sets.json")
                elif parts[2] == "styles":
                    # get_team_styles
                    return load_mock_data("get_team_styles.json")

            elif parts[0] == "projects" and len(parts) >= 3:
                # get_project_files
                return load_mock_data("get_project_files.json")

            elif parts[0] == "components" and len(parts) >= 2:
                # get_component
                return load_mock_data("get_component.json")

            elif parts[0] == "styles" and len(parts) >= 2:
                # get_style
                return load_mock_data("get_style.json")

            # Default mock data
            return {"mock": "data"}

        mock.side_effect = side_effect
        yield mock


# Patch the CacheManager.save_to_cache method
@pytest.fixture
def mock_save_to_cache():
    with patch.object(CacheManager, "save_to_cache") as mock:
        mock.return_value = "/mock/path/to/cache/file.json"
        yield mock


# Test get_file function
@pytest.mark.asyncio
async def test_get_file(mock_make_request, mock_save_to_cache):
    # Test with minimal parameters
    result = await figma_get_file("test_file_key")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key")

    # Verify save_to_cache was called
    mock_save_to_cache.assert_called_once()

    # Verify the result contains expected fields
    assert "file_path" in result
    assert "message" in result
    assert result["file_path"] == "/mock/path/to/cache/file.json"

    # Reset mocks for next test
    mock_make_request.reset_mock()
    mock_save_to_cache.reset_mock()

    # Test with all parameters
    result = await figma_get_file("test_file_key", version="123", depth=2, branch_data=True)

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key?version=123&depth=2&branch_data=True")


# Test get_file_nodes function
@pytest.mark.asyncio
async def test_get_file_nodes(mock_make_request, mock_save_to_cache):
    # Test with minimal parameters
    result = await figma_get_file_nodes("test_file_key", ["node1", "node2"])

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/nodes?ids=node1,node2")

    # Verify save_to_cache was called
    mock_save_to_cache.assert_called_once()

    # Verify the result contains expected fields
    assert "file_path" in result
    assert "message" in result
    assert result["file_path"] == "/mock/path/to/cache/file.json"

    # Reset mocks for next test
    mock_make_request.reset_mock()
    mock_save_to_cache.reset_mock()

    # Test with all parameters
    result = await figma_get_file_nodes("test_file_key", ["node1", "node2"], depth=2, version="123")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/nodes?ids=node1,node2&depth=2&version=123")


# Test get_image function
@pytest.mark.asyncio
async def test_get_image(mock_make_request):
    # Test with minimal parameters
    result = await figma_get_image("test_file_key", ["node1", "node2"])

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/images/test_file_key?ids=node1,node2")

    # Reset mock for next test
    mock_make_request.reset_mock()

    # Test with all parameters
    result = await figma_get_image(
        "test_file_key",
        ["node1", "node2"],
        scale=2.0,
        format_type="png",
        svg_include_id=True,
        svg_simplify_stroke=True,
        use_absolute_bounds=True,
    )

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with(
        "/images/test_file_key?ids=node1,node2&scale=2.0&format=png&svg_include_id=True&svg_simplify_stroke=True&use_absolute_bounds=True"
    )


# Test get_image_fills function
@pytest.mark.asyncio
async def test_get_image_fills(mock_make_request):
    result = await figma_get_image_fills("test_file_key")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/images")


# Test get_comments function
@pytest.mark.asyncio
async def test_get_comments(mock_make_request):
    result = await figma_get_comments("test_file_key")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/comments")


# Test post_comment function
@pytest.mark.asyncio
async def test_post_comment(mock_make_request):
    # Test with minimal parameters
    result = await figma_post_comment("test_file_key", "Test comment")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/comments", "POST", {"message": "Test comment"})

    # Reset mock for next test
    mock_make_request.reset_mock()

    # Test with all parameters
    client_meta = {"x": 100, "y": 200, "node_id": "node1", "node_offset": {"x": 10, "y": 20}}

    result = await figma_post_comment("test_file_key", "Test comment", client_meta=client_meta, comment_id="comment1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with(
        "/files/test_file_key/comments",
        "POST",
        {"message": "Test comment", "client_meta": client_meta, "comment_id": "comment1"},
    )


# Test delete_comment function
@pytest.mark.asyncio
async def test_delete_comment(mock_make_request):
    result = await figma_delete_comment("test_file_key", "comment1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/comments/comment1", "DELETE")


# Test get_team_projects function
@pytest.mark.asyncio
async def test_get_team_projects(mock_make_request):
    # Test with minimal parameters
    result = await figma_get_team_projects("team1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/projects")

    # Reset mock for next test
    mock_make_request.reset_mock()

    # Test with all parameters
    result = await figma_get_team_projects("team1", page_size=10, cursor="cursor1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/projects?page_size=10&cursor=cursor1")


# Test get_project_files function
@pytest.mark.asyncio
async def test_get_project_files(mock_make_request):
    # Test with minimal parameters
    result = await figma_get_project_files("project1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/projects/project1/files")

    # Reset mock for next test
    mock_make_request.reset_mock()

    # Test with all parameters
    result = await figma_get_project_files("project1", page_size=10, cursor="cursor1", branch_data=True)

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/projects/project1/files?page_size=10&cursor=cursor1&branch_data=True")


# Test get_team_components function
@pytest.mark.asyncio
async def test_get_team_components(mock_make_request):
    # Test with minimal parameters
    result = await figma_get_team_components("team1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/components")

    # Reset mock for next test
    mock_make_request.reset_mock()

    # Test with all parameters
    result = await figma_get_team_components("team1", page_size=10, cursor="cursor1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/components?page_size=10&cursor=cursor1")


# Test get_file_components function
@pytest.mark.asyncio
async def test_get_file_components(mock_make_request):
    result = await figma_get_file_components("test_file_key")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/components")


# Test get_component function
@pytest.mark.asyncio
async def test_get_component(mock_make_request):
    result = await figma_get_component("component1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/components/component1")


# Test get_team_component_sets function
@pytest.mark.asyncio
async def test_get_team_component_sets(mock_make_request):
    # Test with minimal parameters
    result = await figma_get_team_component_sets("team1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/component_sets")

    # Reset mock for next test
    mock_make_request.reset_mock()

    # Test with all parameters
    result = await figma_get_team_component_sets("team1", page_size=10, cursor="cursor1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/component_sets?page_size=10&cursor=cursor1")


# Test get_team_styles function
@pytest.mark.asyncio
async def test_get_team_styles(mock_make_request):
    # Test with minimal parameters
    result = await figma_get_team_styles("team1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/styles")

    # Reset mock for next test
    mock_make_request.reset_mock()

    # Test with all parameters
    result = await figma_get_team_styles("team1", page_size=10, cursor="cursor1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/teams/team1/styles?page_size=10&cursor=cursor1")


# Test get_file_styles function
@pytest.mark.asyncio
async def test_get_file_styles(mock_make_request):
    result = await figma_get_file_styles("test_file_key")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/files/test_file_key/styles")


# Test get_style function
@pytest.mark.asyncio
async def test_get_style(mock_make_request):
    result = await figma_get_style("style1")

    # Verify make_request was called with correct parameters
    mock_make_request.assert_called_once_with("/styles/style1")
