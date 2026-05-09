"""
task_list / search_tasks `code` filter (v1.8.4)
================================================

The new exact-match `code` parameter on the search/list path. Codes can be
shared across tasks (since 1.8.2), so the filter returns every matching row.
"""

from unittest.mock import patch

import pytest

from src.security import SecurityError, validate_task_list_params


# =============================================================================
# Validator
# =============================================================================

class TestValidator:
    def test_none_passes_through(self):
        result = validate_task_list_params(limit=10, offset=0)
        assert result[6] is None  # validated_code

    def test_valid_code_returned(self):
        result = validate_task_list_params(limit=10, offset=0, code="OLOM-460")
        assert result[6] == "OLOM-460"

    def test_invalid_format_raises(self):
        with pytest.raises(SecurityError):
            validate_task_list_params(limit=10, offset=0, code="lowercase-1")

    def test_path_traversal_format_rejected(self):
        with pytest.raises(SecurityError):
            validate_task_list_params(limit=10, offset=0, code="..")

    def test_empty_string_rejected(self):
        with pytest.raises(SecurityError):
            validate_task_list_params(limit=10, offset=0, code="")


# =============================================================================
# search_tasks
# =============================================================================

class TestSearchByCode:
    def test_filter_returns_only_matching_code(self, task_store):
        a = task_store.create_task(
            title="Alpha", content="x", tags=["feature"], code="FEAT-100"
        )
        b = task_store.create_task(
            title="Beta", content="y", tags=["feature"], code="FEAT-200"
        )

        tasks, total = task_store.search_tasks(code="FEAT-100")
        assert total == 1
        assert len(tasks) == 1
        assert tasks[0].id == a["task_id"]
        assert tasks[0].code == "FEAT-100"

    def test_filter_returns_all_tasks_sharing_code(self, task_store):
        # Codes are NOT unique post-1.8.2; filter must return EVERY task
        # carrying the exact code.
        a = task_store.create_task(
            title="A", content="x", tags=["feature"], code="DUO-9"
        )
        b = task_store.create_task(
            title="B", content="y", tags=["feature"], code="DUO-9"
        )
        c = task_store.create_task(
            title="C", content="z", tags=["feature"], code="OTHER-9"
        )

        tasks, total = task_store.search_tasks(code="DUO-9", limit=50)
        ids = sorted(t.id for t in tasks)
        assert ids == sorted([a["task_id"], b["task_id"]])
        assert total == 2

    def test_filter_no_match_returns_empty(self, task_store):
        task_store.create_task(
            title="A", content="x", tags=["feature"], code="FEAT-1"
        )
        tasks, total = task_store.search_tasks(code="FEAT-999")
        assert tasks == []
        assert total == 0

    def test_combined_with_status_filter(self, task_store):
        a = task_store.create_task(
            title="A", content="x", tags=["feature"], code="MIX-7"
        )
        b = task_store.create_task(
            title="B", content="y", tags=["feature"], code="MIX-7"
        )
        # Walk B to completed; A stays pending.
        task_store.update_task(task_id=b["task_id"], status="in_progress")
        task_store.update_task(task_id=b["task_id"], status="completed")

        tasks, total = task_store.search_tasks(code="MIX-7", status="pending")
        assert total == 1
        assert tasks[0].id == a["task_id"]

        tasks, total = task_store.search_tasks(code="MIX-7", status="completed")
        assert total == 1
        assert tasks[0].id == b["task_id"]

    def test_combined_with_query_semantic_search(self, task_store):
        # Code filter applies on top of vector search.
        task_store.create_task(
            title="Login bug fix", content="auth issue", tags=["bugfix"],
            code="BUG-1"
        )
        task_store.create_task(
            title="Login UI tweak", content="ui change", tags=["feature"],
            code="BUG-2"
        )
        tasks, total = task_store.search_tasks(query="login", code="BUG-1")
        assert total == 1
        assert tasks[0].code == "BUG-1"
