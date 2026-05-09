"""
Code Field & Auto-Generation Tests
==================================

Tests for the `code` column and auto-generation logic added in task #209:
- src/security.py validate_code helper
- src/task_store.py _generate_code helper, create_task, create_tasks_bulk
- src/models.py Task.code field, from_db_row, to_dict
- DB migration (idempotent ALTER TABLE + UNIQUE partial index)
"""

import pytest

from src.security import validate_code, SecurityError


# =============================================================================
# Regex / format validation
# =============================================================================

class TestValidateCode:
    @pytest.mark.parametrize("code", [
        "FEAT-44",
        "FIX-12",
        "OLOM-460",
        "JIRA-1234",
        "REFACTOR-1",
        "A-1",
    ])
    def test_valid_codes(self, code):
        assert validate_code(code) == code

    @pytest.mark.parametrize("code", [
        "feat-44",       # lowercase
        "FEAT_44",       # underscore
        "FEAT44",        # missing dash
        "FEAT-",         # missing number
        "-44",           # missing prefix
        "FEAT-44a",      # trailing letters
        "FE-AT-44",      # multiple dashes
        "FEAT 44",       # space
        "",              # empty
    ])
    def test_invalid_codes(self, code):
        with pytest.raises(SecurityError):
            validate_code(code)

    def test_max_length(self):
        # 32 chars allowed
        ok = "A" * 30 + "-1"  # 32 chars, valid format
        assert validate_code(ok) == ok
        # 33 chars rejected
        too_long = "A" * 31 + "-1"  # 33 chars
        with pytest.raises(SecurityError):
            validate_code(too_long)

    def test_non_string_rejected(self):
        with pytest.raises(SecurityError):
            validate_code(123)
        with pytest.raises(SecurityError):
            validate_code(None)


# =============================================================================
# Auto-generation logic
# =============================================================================

class TestAutoGeneration:
    def test_default_prefix_when_no_tags(self, task_store):
        result = task_store.create_task(title="No tags", content="Body")
        assert result["success"] is True
        assert result["code"] == "TASK-1"

    def test_default_prefix_when_unmatched_tag(self, task_store):
        result = task_store.create_task(
            title="Unknown tag",
            content="Body",
            tags=["random-thing"],
        )
        assert result["code"] == "TASK-1"

    def test_feature_tag_maps_to_feat(self, task_store):
        result = task_store.create_task(
            title="A feature",
            content="Body",
            tags=["feature"],
        )
        assert result["code"] == "FEAT-1"

    def test_bugfix_tag_maps_to_fix(self, task_store):
        result = task_store.create_task(
            title="A bug",
            content="Body",
            tags=["bugfix"],
        )
        assert result["code"] == "FIX-1"

    @pytest.mark.parametrize("tag,prefix", [
        ("refactor", "REFACTOR"),
        ("docs", "DOCS"),
        ("test", "TEST"),
        ("hotfix", "HOTFIX"),
        ("chore", "CHORE"),
        ("research", "RESEARCH"),
        ("spike", "SPIKE"),
    ])
    def test_all_prefix_mappings(self, task_store, tag, prefix):
        result = task_store.create_task(
            title=f"Tag {tag}",
            content="Body",
            tags=[tag],
        )
        assert result["code"] == f"{prefix}-1"

    def test_first_matching_tag_wins(self, task_store):
        # "feature" comes before "bugfix" in tag list → FEAT wins
        result = task_store.create_task(
            title="Multi-tag",
            content="Body",
            tags=["feature", "bugfix"],
        )
        assert result["code"] == "FEAT-1"

    def test_counter_increments_per_prefix(self, task_store):
        a = task_store.create_task(title="F1", content="x", tags=["feature"])
        b = task_store.create_task(title="F2", content="y", tags=["feature"])
        c = task_store.create_task(title="F3", content="z", tags=["feature"])
        assert a["code"] == "FEAT-1"
        assert b["code"] == "FEAT-2"
        assert c["code"] == "FEAT-3"

    def test_counters_independent_per_prefix(self, task_store):
        f1 = task_store.create_task(title="F1", content="a", tags=["feature"])
        x1 = task_store.create_task(title="X1", content="b", tags=["bugfix"])
        f2 = task_store.create_task(title="F2", content="c", tags=["feature"])
        x2 = task_store.create_task(title="X2", content="d", tags=["bugfix"])
        assert f1["code"] == "FEAT-1"
        assert x1["code"] == "FIX-1"
        assert f2["code"] == "FEAT-2"
        assert x2["code"] == "FIX-2"


# =============================================================================
# Custom code path
# =============================================================================

class TestCustomCode:
    def test_custom_code_accepted(self, task_store):
        result = task_store.create_task(
            title="Jira", content="Body", tags=["feature"], code="OLOM-460"
        )
        assert result["success"] is True
        assert result["code"] == "OLOM-460"

    def test_custom_code_does_not_affect_auto_counter(self, task_store):
        # Custom code with arbitrary prefix shouldn't disturb FEAT counter
        task_store.create_task(title="Custom", content="x", tags=["feature"], code="OLOM-460")
        auto = task_store.create_task(title="Auto", content="y", tags=["feature"])
        assert auto["code"] == "FEAT-1"

    def test_invalid_custom_code_rejected(self, task_store):
        from src.security import SecurityError as SE
        with pytest.raises(SE):
            task_store.create_task(
                title="Bad", content="x", tags=["feature"], code="lowercase-1"
            )

    def test_duplicate_custom_code_rejected(self, task_store):
        first = task_store.create_task(
            title="A", content="alpha", tags=["feature"], code="DUP-1"
        )
        assert first["success"] is True
        # Second insert with same code should fail (UNIQUE partial index)
        with pytest.raises(Exception):
            task_store.create_task(
                title="B", content="beta", tags=["feature"], code="DUP-1"
            )


# =============================================================================
# Bulk creation
# =============================================================================

class TestBulkCodeGeneration:
    def test_bulk_mix_custom_and_auto(self, task_store):
        result = task_store.create_tasks_bulk([
            {"title": "Auto1", "content": "a", "tags": ["feature"]},
            {"title": "Custom", "content": "b", "tags": ["feature"], "code": "OLOM-460"},
            {"title": "Auto2", "content": "c", "tags": ["feature"]},
            {"title": "Bug", "content": "d", "tags": ["bugfix"]},
        ])
        assert result["success"] is True
        ids = result["created_task_ids"]
        assert len(ids) == 4

        tasks = [task_store.get_task_by_id(tid) for tid in ids]
        codes = [t.code for t in tasks]
        assert codes[0] == "FEAT-1"
        assert codes[1] == "OLOM-460"
        assert codes[2] == "FEAT-2"  # counter advances correctly within bulk
        assert codes[3] == "FIX-1"

    def test_bulk_counters_per_prefix(self, task_store):
        result = task_store.create_tasks_bulk([
            {"title": "F1", "content": "1", "tags": ["feature"]},
            {"title": "X1", "content": "2", "tags": ["bugfix"]},
            {"title": "F2", "content": "3", "tags": ["feature"]},
            {"title": "X2", "content": "4", "tags": ["bugfix"]},
        ])
        ids = result["created_task_ids"]
        codes = [task_store.get_task_by_id(tid).code for tid in ids]
        assert codes == ["FEAT-1", "FIX-1", "FEAT-2", "FIX-2"]


# =============================================================================
# Persistence (model + DB roundtrip)
# =============================================================================

class TestCodePersistence:
    def test_get_task_by_id_returns_code(self, task_store):
        result = task_store.create_task(title="Persisted", content="x", tags=["feature"])
        task = task_store.get_task_by_id(result["task_id"])
        assert task is not None
        assert task.code == "FEAT-1"

    def test_to_dict_includes_code(self, task_store):
        result = task_store.create_task(title="Dict", content="x", tags=["bugfix"])
        task = task_store.get_task_by_id(result["task_id"])
        d = task.to_dict()
        assert "code" in d
        assert d["code"] == "FIX-1"

    def test_search_returns_code(self, task_store):
        task_store.create_task(title="Searchable", content="needle", tags=["feature"])
        tasks, _ = task_store.search_tasks(query=None, limit=10)
        assert any(t.code == "FEAT-1" for t in tasks)

    def test_update_task_code_field(self, task_store):
        result = task_store.create_task(title="Updatable", content="x", tags=["feature"])
        tid = result["task_id"]
        task_store.update_task(task_id=tid, code="MIG-7")
        task = task_store.get_task_by_id(tid)
        assert task.code == "MIG-7"

    def test_update_invalid_code_rejected(self, task_store):
        result = task_store.create_task(title="Updatable", content="x", tags=["feature"])
        tid = result["task_id"]
        with pytest.raises(SecurityError):
            task_store.update_task(task_id=tid, code="lowercase-1")


# =============================================================================
# Migration safety
# =============================================================================

class TestMigration:
    def test_migration_idempotent(self, task_store):
        # Re-trigger init multiple times — must not error.
        task_store._db_initialized = False
        task_store._ensure_db_initialized_sync()
        task_store._db_initialized = False
        task_store._ensure_db_initialized_sync()
        result = task_store.create_task(title="Post-migrate", content="x", tags=["feature"])
        assert result["success"] is True
        assert result["code"] == "FEAT-1"

    def test_legacy_null_codes_coexist(self, task_store):
        """Simulate legacy rows with NULL code via direct INSERT, then verify
        that auto-generation continues to work and that NULL codes are loaded
        as None on the Task model."""
        task_store._ensure_db_initialized_sync()
        conn = task_store._get_connection()
        try:
            # Legacy row with NULL code (UNIQUE partial index allows multiple NULLs)
            conn.execute(
                'INSERT INTO tasks (parent_id, status, title, content, content_hash, '
                'created_at, code) VALUES (?, ?, ?, ?, ?, ?, NULL)',
                (None, "pending", "Legacy A", "old", "legacy_a_hash", "2020-01-01T00:00:00"),
            )
            conn.execute(
                'INSERT INTO tasks (parent_id, status, title, content, content_hash, '
                'created_at, code) VALUES (?, ?, ?, ?, ?, ?, NULL)',
                (None, "pending", "Legacy B", "older", "legacy_b_hash", "2020-01-02T00:00:00"),
            )
            conn.commit()
        finally:
            conn.close()

        # Auto-gen on a fresh task — counter ignores NULL legacy rows
        result = task_store.create_task(title="New", content="x", tags=["feature"])
        assert result["code"] == "FEAT-1"

        # search returns legacy rows with code=None
        tasks, _ = task_store.search_tasks(query=None, limit=50)
        legacy_codes = [t.code for t in tasks if t.title.startswith("Legacy")]
        assert legacy_codes == [None, None] or set(legacy_codes) == {None}