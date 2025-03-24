import pytest

from mcp_toolbox.enhance.memory import LocalMemory, MemoryModel


@pytest.fixture
def memory_file(tmp_path):
    return tmp_path / "test-memory"


@pytest.fixture
def local_memory(memory_file):
    memory = LocalMemory("test-session", memory_file)
    # Ensure the file is empty at the start of each test
    memory.clear()
    return memory


def test_memory_basic(local_memory: LocalMemory):
    """Test basic memory operations"""
    assert local_memory.session_id == "test-session"

    # Store and query
    memory_model = local_memory.store("test-brief", "test-detail")
    assert isinstance(memory_model, MemoryModel)
    assert memory_model.session_id == "test-session"
    assert memory_model.brief == "test-brief"
    assert memory_model.detail == "test-detail"
    assert memory_model.embedding is not None

    # Query
    results = local_memory.query("test-brief")
    assert len(results) == 1
    assert results[0].brief == "test-brief"
    assert results[0].detail == "test-detail"
    assert results[0].session_id == "test-session"


def test_memory_cross_session(memory_file):
    """Test cross-session memory operations"""
    # Create two memory instances with different session IDs
    memory1 = LocalMemory("session-1", memory_file)
    memory1.clear()  # Start with a clean file

    # Store a memory in session 1
    memory1.store("brief-1", "detail-1")

    # Create a second memory instance with a different session ID
    memory2 = LocalMemory("session-2", memory_file)

    # Store a memory in session 2
    memory2.store("brief-2", "detail-2")

    # Refresh memory1 to see both entries
    memory1.current_memory = memory1._load()

    # Query with cross_session=True (default)
    results1 = memory1.query("brief", top_k=5, refresh=True)
    assert len(results1) == 2, f"Expected 2 results, got {len(results1)}: {results1}"

    # Query with cross_session=False
    results2 = memory1.query("brief", top_k=5, cross_session=False)
    assert len(results2) == 1, f"Expected 1 result, got {len(results2)}: {results2}"
    assert results2[0].session_id == "session-1"

    results3 = memory2.query("brief", top_k=5, cross_session=False)
    assert len(results3) == 1, f"Expected 1 result, got {len(results3)}: {results3}"
    assert results3[0].session_id == "session-2"


def test_memory_clear(memory_file):
    """Test clearing memory"""
    # Create a new memory instance
    memory = LocalMemory("test-session", memory_file)
    memory.clear()  # Start with a clean file

    # Store some memories
    memory.store("brief-1", "detail-1")
    memory.store("brief-2", "detail-2")

    # Verify memories are stored
    results = memory.query("brief", top_k=5)
    assert len(results) == 2, f"Expected 2 results, got {len(results)}: {results}"

    # Clear memories
    memory.clear()

    # Verify memories are cleared
    results = memory.query("brief", top_k=5)
    assert len(results) == 0, f"Expected 0 results, got {len(results)}: {results}"


def test_memory_empty_file(memory_file):
    """Test handling of empty memory file"""
    # Create a new memory instance with a non-existent file
    memory = LocalMemory("test-session", memory_file)
    memory.clear()  # Start with a clean file

    # Query should return empty list
    results = memory.query("test")
    assert len(results) == 0

    # Store should work even with empty file
    memory.store("test-brief", "test-detail")
    results = memory.query("test")
    assert len(results) == 1


def test_memory_top_k(memory_file):
    """Test top_k parameter in query"""
    # Create a new memory instance
    memory = LocalMemory("test-session", memory_file)
    memory.clear()  # Start with a clean file

    # Store multiple memories with distinct embeddings
    memory.store("apple", "A fruit")
    memory.store("banana", "A yellow fruit")
    memory.store("orange", "A citrus fruit")
    memory.store("grape", "A small fruit")

    # Query with different top_k values
    results1 = memory.query("fruit", top_k=2)
    assert len(results1) == 2, f"Expected 2 results, got {len(results1)}: {results1}"

    results2 = memory.query("fruit", top_k=4)
    assert len(results2) == 4, f"Expected 4 results, got {len(results2)}: {results2}"

    # Query with top_k larger than available results
    results3 = memory.query("fruit", top_k=10)
    assert len(results3) == 4, f"Expected 4 results, got {len(results3)}: {results3}"


def test_memory_refresh(memory_file):
    """Test refresh parameter in query"""
    # Create two memory instances with the same session ID and file
    memory1 = LocalMemory("same-session", memory_file)
    memory1.clear()  # Start with a clean file

    memory2 = LocalMemory("same-session", memory_file)

    # Store a memory using the first instance
    memory1.store("test-brief", "test-detail")

    # Query using the second instance without refresh
    results1 = memory2.query("test", refresh=False)
    assert len(results1) == 0, f"Expected 0 results, got {len(results1)}: {results1}"

    # Query using the second instance with refresh
    results2 = memory2.query("test", refresh=True)
    assert len(results2) == 1, f"Expected 1 result, got {len(results2)}: {results2}"
