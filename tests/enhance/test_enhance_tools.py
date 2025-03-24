from unittest.mock import patch

import pytest

from mcp_toolbox.enhance.memory import LocalMemory, MemoryModel
from mcp_toolbox.enhance.tools import forget, get_session_id, recall, remember, think


@pytest.mark.asyncio
async def test_think_returns_dict():
    """Test that the think function returns a dictionary."""
    result = await think("Test thought")
    assert isinstance(result, dict), "think() should return a dictionary"


@pytest.mark.asyncio
async def test_think_returns_correct_thought():
    """Test that the returned dictionary contains the input thought."""
    test_thought = "This is a test thought"
    result = await think(test_thought)
    assert result == {"thought": test_thought}, "think() should return a dictionary with the input thought"


@pytest.mark.asyncio
async def test_think_with_different_thought_types():
    """Test think() with various types of thoughts."""
    test_cases = [
        "Simple string thought",
        "Thought with special characters: !@#$%^&*()",
        "Thought with numbers: 12345",
        "Thought with unicode: こんにちは 世界",
        "",  # Empty string
    ]

    for test_thought in test_cases:
        result = await think(test_thought)
        assert result == {"thought": test_thought}, f"Failed for thought: {test_thought}"


@pytest.fixture
def memory_file(tmp_path):
    return tmp_path / "test-memory"


@pytest.fixture
def mock_memory(memory_file):
    memory = LocalMemory("test-session", memory_file)
    memory.clear()  # Start with a clean file
    return memory


@patch("mcp_toolbox.enhance.tools.get_current_session_memory")
def test_get_session_id(mock_get_memory, mock_memory):
    """Test that get_session_id returns the correct session ID."""
    mock_get_memory.return_value = mock_memory

    result = get_session_id()

    assert result == {"session_id": "test-session"}
    mock_get_memory.assert_called_once()


@patch("mcp_toolbox.enhance.tools.get_current_session_memory")
def test_remember(mock_get_memory, mock_memory):
    """Test that remember stores a memory and returns the correct data."""
    mock_get_memory.return_value = mock_memory

    result = remember("test-brief", "test-detail")

    assert result == {
        "session_id": "test-session",
        "brief": "test-brief",
        "detail": "test-detail",
    }
    mock_get_memory.assert_called_once()

    # Verify the memory was stored
    memories = mock_memory.query("test-brief")
    assert len(memories) == 1
    assert memories[0].brief == "test-brief"
    assert memories[0].detail == "test-detail"


@patch("mcp_toolbox.enhance.tools.get_current_session_memory")
def test_recall_current_session(mock_get_memory, mock_memory):
    """Test that recall retrieves memories from the current session."""
    mock_get_memory.return_value = mock_memory

    # Store some memories
    mock_memory.store("brief-1", "detail-1")
    mock_memory.store("brief-2", "detail-2")

    # Recall with default parameters (current session)
    result = recall("brief")

    assert len(result) == 2
    assert all(isinstance(item, dict) for item in result)
    assert all("session_id" in item and "brief" in item and "detail" in item for item in result)
    mock_get_memory.assert_called()


@patch("mcp_toolbox.enhance.tools.LocalMemory.use_session")
def test_recall_specific_session(mock_use_session, mock_memory):
    """Test that recall retrieves memories from a specific session."""
    mock_use_session.return_value = mock_memory

    # Store some memories
    mock_memory.store("brief-1", "detail-1")

    # Recall with specific session ID
    result = recall("brief", session_id="specific-session")

    assert len(result) == 1
    mock_use_session.assert_called_once_with("specific-session")


@patch("mcp_toolbox.enhance.tools.get_current_session_memory")
def test_recall_cross_session(mock_get_memory, mock_memory):
    """Test that recall retrieves memories across sessions when cross_session is True."""
    mock_get_memory.return_value = mock_memory

    # Mock the query method to simulate cross-session behavior
    original_query = mock_memory.query

    def mock_query(query_text, top_k=3, cross_session=True):
        if cross_session:
            return [
                MemoryModel(session_id="session-1", brief="brief-1", detail="detail-1"),
                MemoryModel(session_id="session-2", brief="brief-2", detail="detail-2"),
            ]
        else:
            return [MemoryModel(session_id="test-session", brief="brief-1", detail="detail-1")]

    mock_memory.query = mock_query

    # Recall with cross_session=True
    result = recall("brief", cross_session=True)

    assert len(result) == 2
    assert result[0]["session_id"] == "session-1"
    assert result[1]["session_id"] == "session-2"

    # Recall with cross_session=False
    result = recall("brief", cross_session=False)

    assert len(result) == 1
    assert result[0]["session_id"] == "test-session"

    # Restore original query method
    mock_memory.query = original_query


@patch("mcp_toolbox.enhance.tools.get_current_session_memory")
def test_recall_top_k(mock_get_memory, mock_memory):
    """Test that recall respects the top_k parameter."""
    mock_get_memory.return_value = mock_memory

    # Store multiple memories
    for i in range(10):
        mock_memory.store(f"brief-{i}", f"detail-{i}")

    # Recall with top_k=3
    result = recall("brief", top_k=3)

    assert len(result) <= 3
    mock_get_memory.assert_called()


@patch("mcp_toolbox.enhance.tools.get_current_session_memory")
def test_forget(mock_get_memory, mock_memory):
    """Test that forget clears all memories."""
    mock_get_memory.return_value = mock_memory

    # Store some memories
    mock_memory.store("brief-1", "detail-1")
    mock_memory.store("brief-2", "detail-2")

    # Verify memories are stored
    assert len(mock_memory.query("brief")) == 2

    # Forget all memories
    result = forget()

    assert result == {"message": "All memories are cleared."}
    mock_get_memory.assert_called()

    # Verify memories are cleared
    assert len(mock_memory.query("brief")) == 0
