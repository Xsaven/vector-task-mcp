"""
Pytest Configuration and Fixtures
=================================

Shared fixtures and configuration for vector-task-mcp tests.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Generator
import tempfile
import shutil
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Mock Fixtures for External Dependencies
# =============================================================================

@pytest.fixture
def mock_embedding_model():
    """
    Mock embedding model to avoid loading sentence-transformers.

    Returns a mock that produces consistent 384-dimensional embeddings
    based on the input text hash for reproducibility.
    """
    mock_model = Mock()

    def encode_single(text: str) -> np.ndarray:
        """Generate deterministic 384D embedding from text hash."""
        # Use hash to create reproducible embeddings
        text_hash = hash(text) % 2**32
        np.random.seed(text_hash)
        return np.random.rand(384).astype(np.float32)

    def encode(texts: list) -> np.ndarray:
        """Batch encode multiple texts."""
        return np.array([encode_single(t) for t in texts])

    mock_model.encode_single = encode_single
    mock_model.encode = encode

    return mock_model


@pytest.fixture
def mock_sqlite_vec():
    """
    Mock sqlite-vec extension loading for tests that don't need actual vector search.
    """
    with patch('sqlite_vec.load') as mock_load:
        mock_load.return_value = None
        yield mock_load


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def temp_db_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test database.

    Yields:
        Path to temporary directory (auto-cleaned after test)
    """
    temp_dir = tempfile.mkdtemp(prefix="vector_task_test_")
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db_path(temp_db_dir: Path) -> Path:
    """
    Create path for temporary test database.

    Args:
        temp_db_dir: Temporary directory from fixture

    Returns:
        Path to test database file
    """
    return temp_db_dir / "test_tasks.db"


@pytest.fixture
def task_store(temp_db_path: Path, mock_embedding_model):
    """
    Create TaskStore instance with mock embedding model.

    This fixture provides an isolated TaskStore for each test,
    using a temporary database and mocked embeddings.

    Args:
        temp_db_path: Path to temporary database
        mock_embedding_model: Mocked embedding model

    Yields:
        Configured TaskStore instance
    """
    from src.task_store import TaskStore

    # Patch the embedding model getter
    with patch('src.task_store.get_embedding_model', return_value=mock_embedding_model):
        store = TaskStore(db_path=temp_db_path)
        yield store


# =============================================================================
# Task Hierarchy Fixtures
# =============================================================================

@pytest.fixture
def simple_hierarchy(task_store) -> dict:
    """
    Create a simple 2-level task hierarchy for testing.

    Structure:
        Root (pending)
        └── Child (pending)

    Returns:
        Dict with 'root_id' and 'child_id' keys
    """
    root = task_store.create_task(
        title="Root Task",
        content="Root level task for testing"
    )
    child = task_store.create_task(
        title="Child Task",
        content="Child level task for testing",
        parent_id=root['task_id']
    )

    return {
        'root_id': root['task_id'],
        'child_id': child['task_id']
    }


@pytest.fixture
def deep_hierarchy(task_store) -> dict:
    """
    Create a 4-level deep task hierarchy for testing status propagation.

    Structure:
        Level0 (Root)
        └── Level1
            └── Level2
                └── Level3 (Leaf)

    All tasks start with 'pending' status.

    Returns:
        Dict with 'level0_id', 'level1_id', 'level2_id', 'level3_id' keys
    """
    # Level 0 - Root
    level0 = task_store.create_task(
        title="Level 0 - Root",
        content="Root level task (depth 0)"
    )
    level0_id = level0['task_id']

    # Level 1
    level1 = task_store.create_task(
        title="Level 1 - Parent",
        content="First level child (depth 1)",
        parent_id=level0_id
    )
    level1_id = level1['task_id']

    # Level 2
    level2 = task_store.create_task(
        title="Level 2 - Grandchild",
        content="Second level child (depth 2)",
        parent_id=level1_id
    )
    level2_id = level2['task_id']

    # Level 3 - Leaf
    level3 = task_store.create_task(
        title="Level 3 - Leaf",
        content="Third level child (depth 3) - deepest task",
        parent_id=level2_id
    )
    level3_id = level3['task_id']

    return {
        'level0_id': level0_id,
        'level1_id': level1_id,
        'level2_id': level2_id,
        'level3_id': level3_id
    }


@pytest.fixture
def multi_child_hierarchy(task_store) -> dict:
    """
    Create a hierarchy with multiple children at each level.

    Structure:
        Root
        ├── Child1
        │   ├── Grandchild1A
        │   └── Grandchild1B
        └── Child2
            └── Grandchild2A

    Returns:
        Dict with all task IDs
    """
    root = task_store.create_task(
        title="Root",
        content="Root with multiple children"
    )
    root_id = root['task_id']

    child1 = task_store.create_task(
        title="Child 1",
        content="First child",
        parent_id=root_id
    )
    child1_id = child1['task_id']

    child2 = task_store.create_task(
        title="Child 2",
        content="Second child",
        parent_id=root_id
    )
    child2_id = child2['task_id']

    gc1a = task_store.create_task(
        title="Grandchild 1A",
        content="First grandchild of Child 1",
        parent_id=child1_id
    )
    gc1b = task_store.create_task(
        title="Grandchild 1B",
        content="Second grandchild of Child 1",
        parent_id=child1_id
    )
    gc2a = task_store.create_task(
        title="Grandchild 2A",
        content="First grandchild of Child 2",
        parent_id=child2_id
    )

    return {
        'root_id': root_id,
        'child1_id': child1_id,
        'child2_id': child2_id,
        'gc1a_id': gc1a['task_id'],
        'gc1b_id': gc1b['task_id'],
        'gc2a_id': gc2a['task_id']
    }


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def sample_task_data():
    """
    Provide sample task data for testing.

    Returns:
        List of dicts with task parameters
    """
    return [
        {
            "title": "Implement authentication",
            "content": "Add JWT-based user authentication",
            "priority": "high",
            "tags": ["backend", "security"]
        },
        {
            "title": "Write unit tests",
            "content": "Add comprehensive test coverage",
            "priority": "medium",
            "tags": ["testing", "quality"]
        },
        {
            "title": "Update documentation",
            "content": "Document API endpoints and usage",
            "priority": "low",
            "tags": ["docs"]
        }
    ]


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring full setup"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that may take longer to execute"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmark tests"
    )