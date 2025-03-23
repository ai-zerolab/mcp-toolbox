import pytest

from mcp_toolbox.enhance.tools import think


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
