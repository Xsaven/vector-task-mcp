"""
TaskStore Unit Tests
====================

Tests for src/task_store.py including:
- Task CRUD operations
- Status propagation in hierarchies
- Deep hierarchy status propagation (4 levels)
- Parent-child relationship management
"""

import pytest
from unittest.mock import patch
from pathlib import Path


class TestDeepHierarchyStatusPropagation:
    """
    Test suite for deep hierarchy status propagation.

    Verifies that status changes in deeply nested tasks correctly
    propagate up through the entire parent chain to the root.

    Bug context (memory #72):
    - When deep nested subtasks complete (3+ levels deep), parent tasks
      at certain depths remained `in_progress` instead of updating correctly.
    - Fix: Continue recursion to grandparent even when siblings not finished.
    """

    def test_deep_hierarchy_tested_status_propagation(self, task_store, deep_hierarchy):
        """
        Test that 'tested' status propagates correctly and parents get 'completed'.

        Expected behavior:
        - Child with 'tested' status counts as finished
        - Parent should get 'completed' (not 'tested') when all children finish
        - This tests the fix for tested/validated status propagation
        """
        level0_id = deep_hierarchy['level0_id']
        level1_id = deep_hierarchy['level1_id']
        level2_id = deep_hierarchy['level2_id']
        level3_id = deep_hierarchy['level3_id']

        # Start and complete with 'tested' status at leaf
        task_store.update_task(level3_id, status='in_progress')
        task_store.update_task(level3_id, status='tested')

        # Verify all parents got 'completed' (not 'tested')
        for task_id, level_name in [
            (level2_id, "Level2"),
            (level1_id, "Level1"),
            (level0_id, "Root")
        ]:
            task = task_store.get_task_by_id(task_id)
            assert task.status == 'completed', (
                f"{level_name} (id={task_id}) should be 'completed' (not 'tested'). "
                f"Parent tasks always get 'completed' when children finish. "
                f"Actual status: {task.status}"
            )

    def test_deep_hierarchy_validated_status_propagation(self, task_store, deep_hierarchy):
        """
        Test that 'validated' status propagates correctly and parents get 'completed'.

        Same as tested, but with 'validated' status.
        """
        level0_id = deep_hierarchy['level0_id']
        level1_id = deep_hierarchy['level1_id']
        level2_id = deep_hierarchy['level2_id']
        level3_id = deep_hierarchy['level3_id']

        # Start and complete with 'validated' status at leaf
        task_store.update_task(level3_id, status='in_progress')
        task_store.update_task(level3_id, status='validated')

        # Verify all parents got 'completed' (not 'validated')
        for task_id, level_name in [
            (level2_id, "Level2"),
            (level1_id, "Level1"),
            (level0_id, "Root")
        ]:
            task = task_store.get_task_by_id(task_id)
            assert task.status == 'completed', (
                f"{level_name} should be 'completed' not 'validated'. "
                f"Actual: {task.status}"
            )


class TestStatusPropagationEdgeCases:
    """
    Edge case tests for status propagation.
    """

    def test_root_task_no_parent_propagation(self, task_store):
        """
        Test that root tasks (no parent) don't cause errors on status change.
        """
        root = task_store.create_task(
            title="Root Only",
            content="A standalone root task"
        )
        root_id = root['task_id']

        # Should not raise any errors
        task_store.update_task(root_id, status='in_progress')
        task = task_store.get_task_by_id(root_id)
        assert task.status == 'in_progress'

        task_store.update_task(root_id, status='completed')
        task = task_store.get_task_by_id(root_id)
        assert task.status == 'completed'

    def test_mixed_finish_statuses_complete_parent(self, task_store):
        """
        Test that parent completes when children have mixed finish statuses.

        Child1: completed
        Child2: tested
        Child3: validated

        Parent should become 'completed' when all are finished.
        """
        root = task_store.create_task(title="Root", content="Root task")
        root_id = root['task_id']

        child1 = task_store.create_task(
            title="Child 1", content="First", parent_id=root_id
        )
        child2 = task_store.create_task(
            title="Child 2", content="Second", parent_id=root_id
        )
        child3 = task_store.create_task(
            title="Child 3", content="Third", parent_id=root_id
        )

        # Complete children with different statuses
        task_store.update_task(child1['task_id'], status='in_progress')
        task_store.update_task(child1['task_id'], status='completed')

        task_store.update_task(child2['task_id'], status='in_progress')
        task_store.update_task(child2['task_id'], status='tested')

        task_store.update_task(child3['task_id'], status='in_progress')
        task_store.update_task(child3['task_id'], status='validated')

        # Root should be completed
        root_task = task_store.get_task_by_id(root_id)
        assert root_task.status == 'completed', (
            "Root should be 'completed' when all children have finish statuses. "
            f"Actual: {root_task.status}"
        )


class TestTaskCRUD:
    """
    Basic CRUD operation tests for TaskStore.
    """

    def test_create_task(self, task_store):
        """Test basic task creation."""
        result = task_store.create_task(
            title="Test Task",
            content="Test content"
        )

        assert result['success'] is True
        assert result['task_id'] > 0
        assert result['status'] == 'pending'

    def test_create_task_with_parent(self, task_store):
        """Test creating child task with parent_id."""
        parent = task_store.create_task(title="Parent", content="Parent content")
        child = task_store.create_task(
            title="Child",
            content="Child content",
            parent_id=parent['task_id']
        )

        assert child['success'] is True

        # Verify relationship
        child_task = task_store.get_task_by_id(child['task_id'])
        assert child_task.parent_id == parent['task_id']

    def test_update_task_status(self, task_store):
        """Test updating task status."""
        result = task_store.create_task(title="Task", content="Content")
        task_id = result['task_id']

        # Update to in_progress
        update_result = task_store.update_task(task_id, status='in_progress')
        assert update_result['success'] is True
        assert update_result['task']['status'] == 'in_progress'

    def test_delete_task(self, task_store):
        """Test task deletion."""
        result = task_store.create_task(title="To Delete", content="Will be deleted")
        task_id = result['task_id']

        deleted = task_store.delete_task(task_id)
        assert deleted is True

        # Verify task no longer exists
        task = task_store.get_task_by_id(task_id)
        assert task is None

    def test_get_task_by_id(self, task_store):
        """Test retrieving task by ID."""
        result = task_store.create_task(
            title="Retrieve Me",
            content="Content to retrieve",
            priority="high"
        )
        task_id = result['task_id']

        task = task_store.get_task_by_id(task_id)
        assert task is not None
        assert task.id == task_id
        assert task.title == "Retrieve Me"
        assert task.priority == "high"

    def test_get_nonexistent_task(self, task_store):
        """Test retrieving non-existent task returns None."""
        task = task_store.get_task_by_id(99999)
        assert task is None


class TestTaskSearch:
    """
    Tests for task search and filtering functionality.
    """

    def test_search_by_status(self, task_store, sample_task_data):
        """Test filtering tasks by status."""
        # Create tasks
        for data in sample_task_data:
            task_store.create_task(**data)

        # Get first task and set to in_progress
        tasks, _ = task_store.search_tasks(limit=10)
        if tasks:
            task_store.update_task(tasks[0].id, status='in_progress')

        # Search by status
        in_progress_tasks, count = task_store.search_tasks(status='in_progress')
        assert count >= 1
        for task in in_progress_tasks:
            assert task.status == 'in_progress'

    def test_search_by_parent_id(self, task_store, simple_hierarchy):
        """Test filtering tasks by parent_id."""
        root_id = simple_hierarchy['root_id']

        children, count = task_store.search_tasks(parent_id=root_id)
        assert count == 1
        assert children[0].parent_id == root_id

    def test_search_with_query(self, task_store, sample_task_data):
        """Test semantic search with query."""
        # Create tasks
        for data in sample_task_data:
            task_store.create_task(**data)

        # Search with query
        results, count = task_store.search_tasks(query="authentication security")
        assert count > 0


class TestTaskStats:
    """
    Tests for task statistics functionality.
    """

    def test_get_stats_empty_db(self, task_store):
        """Test stats on empty database."""
        stats = task_store.get_stats()
        assert stats.total_tasks == 0
        assert stats.pending_count == 0
        assert stats.in_progress_count == 0

    def test_get_stats_with_tasks(self, task_store, sample_task_data):
        """Test stats with existing tasks."""
        # Create tasks
        for data in sample_task_data:
            task_store.create_task(**data)

        stats = task_store.get_stats()
        assert stats.total_tasks == len(sample_task_data)
        assert stats.pending_count == len(sample_task_data)  # All start as pending


class TestParentCompletionValidation:
    """
    Tests for parent task completion validation.

    Verifies that parent tasks cannot be manually set to finish statuses
    (completed/tested/validated) when they have unfinished children.
    This enforces the rule: only complete children, parents auto-propagate.
    """

    def test_cannot_complete_parent_with_pending_children(self, task_store):
        """
        Test that parent cannot be set to 'completed' when children are pending.
        """
        parent = task_store.create_task(title="Parent", content="Parent task")
        parent_id = parent['task_id']

        # Create pending children
        task_store.create_task(title="Child 1", content="First child", parent_id=parent_id)
        task_store.create_task(title="Child 2", content="Second child", parent_id=parent_id)

        # Try to complete parent - should fail
        result = task_store.update_task(parent_id, status='completed')

        assert result['success'] is False
        assert 'unfinished child' in result['message'].lower()
        assert 'error' in result

        # Verify parent still pending
        parent_task = task_store.get_task_by_id(parent_id)
        assert parent_task.status == 'pending'

    def test_cannot_complete_parent_with_in_progress_children(self, task_store):
        """
        Test that parent cannot be set to 'completed' when children are in_progress.
        """
        parent = task_store.create_task(title="Parent", content="Parent task")
        parent_id = parent['task_id']

        child = task_store.create_task(title="Child", content="Child task", parent_id=parent_id)
        task_store.update_task(child['task_id'], status='in_progress')

        # Try to complete parent - should fail
        result = task_store.update_task(parent_id, status='completed')

        assert result['success'] is False
        assert 'unfinished child' in result['message'].lower()

    def test_cannot_validate_parent_with_pending_children(self, task_store):
        """
        Test that parent cannot be set to 'validated' when children are pending.
        """
        parent = task_store.create_task(title="Parent", content="Parent task")
        parent_id = parent['task_id']

        task_store.create_task(title="Child", content="Child task", parent_id=parent_id)

        # Try to validate parent - should fail
        result = task_store.update_task(parent_id, status='validated')

        assert result['success'] is False
        assert 'unfinished child' in result['message'].lower()

    def test_can_complete_parent_when_all_children_finished(self, task_store):
        """
        Test that parent CAN be manually completed when all children are finished.
        (Though normally auto-propagation handles this)
        """
        parent = task_store.create_task(title="Parent", content="Parent task")
        parent_id = parent['task_id']

        child1 = task_store.create_task(title="Child 1", content="First", parent_id=parent_id)
        child2 = task_store.create_task(title="Child 2", content="Second", parent_id=parent_id)

        # Complete all children
        task_store.update_task(child1['task_id'], status='in_progress')
        task_store.update_task(child1['task_id'], status='completed')
        task_store.update_task(child2['task_id'], status='in_progress')
        task_store.update_task(child2['task_id'], status='validated')

        # Parent should already be completed via propagation
        parent_task = task_store.get_task_by_id(parent_id)
        assert parent_task.status == 'completed'

        # Manual update to 'tested' should also work
        result = task_store.update_task(parent_id, status='tested')
        assert result['success'] is True

    def test_can_complete_parent_when_children_canceled(self, task_store):
        """
        Test that canceled children don't block parent completion.
        """
        parent = task_store.create_task(title="Parent", content="Parent task")
        parent_id = parent['task_id']

        child1 = task_store.create_task(title="Child 1", content="First", parent_id=parent_id)
        child2 = task_store.create_task(title="Child 2", content="Second", parent_id=parent_id)

        # Complete one, cancel another
        task_store.update_task(child1['task_id'], status='in_progress')
        task_store.update_task(child1['task_id'], status='completed')
        task_store.update_task(child2['task_id'], status='canceled')

        # Try to validate parent - should succeed (completed + canceled = all finished)
        result = task_store.update_task(parent_id, status='validated')
        assert result['success'] is True

    def test_error_message_includes_unfinished_children_info(self, task_store):
        """
        Test that error message includes details about unfinished children.
        """
        parent = task_store.create_task(title="Parent", content="Parent task")
        parent_id = parent['task_id']

        task_store.create_task(title="Pending Child", content="Still pending", parent_id=parent_id)
        child2 = task_store.create_task(title="Working Child", content="In progress", parent_id=parent_id)
        task_store.update_task(child2['task_id'], status='in_progress')

        result = task_store.update_task(parent_id, status='completed')

        assert result['success'] is False
        # Should mention count
        assert '2 unfinished' in result['message']
        # Should list children
        assert 'Pending Child' in result['message'] or 'Working Child' in result['message']


class TestBulkOperations:
    """
    Tests for bulk task operations.
    """

    def test_create_tasks_bulk(self, task_store):
        """Test bulk task creation."""
        tasks_to_create = [
            {"title": "Bulk Task 1", "content": "Content 1"},
            {"title": "Bulk Task 2", "content": "Content 2"},
            {"title": "Bulk Task 3", "content": "Content 3"},
        ]

        result = task_store.create_tasks_bulk(tasks_to_create)
        assert result['success'] is True
        assert result['count'] == 3
        assert len(result['created_task_ids']) == 3

    def test_delete_tasks_bulk(self, task_store):
        """Test bulk task deletion."""
        # Create tasks first
        task_ids = []
        for i in range(3):
            result = task_store.create_task(
                title=f"Delete Task {i}",
                content=f"Content {i}"
            )
            task_ids.append(result['task_id'])

        # Delete in bulk
        result = task_store.delete_tasks_bulk(task_ids)
        assert result['success'] is True
        assert result['deleted_count'] == 3

        # Verify all deleted
        for task_id in task_ids:
            task = task_store.get_task_by_id(task_id)
            assert task is None


class TestTagNormalization:
    """
    Tests for tag normalization functionality.
    """

    def test_get_all_tags_with_counts(self, task_store):
        """Test getting all tags with usage counts."""
        task_store.create_task(title="Task 1", content="Content", tags=["auth", "backend"])
        task_store.create_task(title="Task 2", content="Content", tags=["auth", "frontend"])
        task_store.create_task(title="Task 3", content="Content", tags=["backend", "api"])

        tag_counts = task_store.get_all_tags_with_counts()

        assert tag_counts.get("auth") == 2
        assert tag_counts.get("backend") == 2
        assert tag_counts.get("frontend") == 1
        assert tag_counts.get("api") == 1

    def test_migrate_tags(self, task_store):
        """Test tag migration with mapping."""
        task_store.create_task(title="Task 1", content="Content", tags=["auth", "backend"])
        task_store.create_task(title="Task 2", content="Content", tags=["authentication", "frontend"])

        mapping = {"authentication": "auth"}
        result = task_store.migrate_tags(mapping)

        assert result['success'] is True
        assert result['tags_replaced'] == 1
        assert result['tasks_updated'] == 1

        task1 = task_store.get_task_by_id(1)
        task2 = task_store.get_task_by_id(2)

        assert "auth" in task1.tags
        assert "authentication" not in task2.tags
        assert "auth" in task2.tags

    def test_migrate_tags_empty_mapping(self, task_store):
        """Test that empty mapping does nothing."""
        task_store.create_task(title="Task", content="Content", tags=["auth"])

        result = task_store.migrate_tags({})

        assert result['success'] is True
        assert result['tasks_updated'] == 0
        assert result['tags_replaced'] == 0

    def test_migrate_tags_preserves_other_tags(self, task_store):
        """Test that migration preserves non-mapped tags."""
        task_store.create_task(title="Task", content="Content", tags=["auth", "backend", "api"])

        mapping = {"auth": "authentication"}
        result = task_store.migrate_tags(mapping)

        assert result['success'] is True

        task = task_store.get_task_by_id(1)
        assert "authentication" in task.tags
        assert "backend" in task.tags
        assert "api" in task.tags
        assert "auth" not in task.tags

    def test_migrate_tags_stores_variants(self, task_store):
        """Test that migrate_tags stores original tags in tag_variants."""
        task_store.create_task(title="Task", content="Content", tags=["auth", "backend"])

        mapping = {"auth": "authentication"}
        result = task_store.migrate_tags(mapping)

        assert result['success'] is True

        task = task_store.get_task_by_id(1)
        assert "authentication" in task.tags
        assert "auth" in task.tag_variants

    def test_migrate_tags_preserves_existing_variants(self, task_store):
        """Test that existing tag_variants are preserved."""
        task_store.create_task(title="Task", content="Content", tags=["auth"])

        mapping1 = {"auth": "authentication"}
        task_store.migrate_tags(mapping1)

        mapping2 = {"backend": "api"}
        task_store.migrate_tags(mapping2)

        task = task_store.get_task_by_id(1)
        assert "auth" in task.tag_variants


class TestTagVariants:
    """
    Tests for tag_variants (alias scent) functionality.
    """

    def test_new_task_has_empty_variants(self, task_store):
        """Test that new tasks have empty tag_variants."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["api", "backend"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        assert task.tag_variants == []

    def test_tag_variants_in_to_dict(self, task_store):
        """Test that tag_variants is included in to_dict()."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["api"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        task_dict = task.to_dict()

        assert "tag_variants" in task_dict
        assert task_dict["tag_variants"] == []


class TestCanonicalTagManagement:
    """
    Tests for canonical tag management functionality.
    """

    def test_add_canonical_mapping(self, task_store):
        """Test adding a canonical tag mapping."""
        result = task_store.add_canonical_mapping("auth", "authentication")

        assert result['success'] is True
        assert result['canonical_tag'] == "auth"
        assert result['variant_tag'] == "authentication"

    def test_add_canonical_mapping_duplicate_variant(self, task_store):
        """Test that duplicate variant fails."""
        task_store.add_canonical_mapping("auth", "authentication")

        result = task_store.add_canonical_mapping("login", "authentication")

        assert result['success'] is False
        assert "already mapped" in result['error']

    def test_add_canonical_mapping_same_tags(self, task_store):
        """Test that mapping same tag to itself fails."""
        result = task_store.add_canonical_mapping("auth", "auth")

        assert result['success'] is False
        assert "cannot be the same" in result['error']

    def test_remove_canonical_mapping(self, task_store):
        """Test removing a canonical tag mapping."""
        task_store.add_canonical_mapping("auth", "authentication")

        result = task_store.remove_canonical_mapping("authentication")

        assert result['success'] is True

        mappings = task_store.get_canonical_mappings()
        assert "authentication" not in mappings

    def test_remove_canonical_mapping_not_found(self, task_store):
        """Test removing non-existent mapping."""
        result = task_store.remove_canonical_mapping("nonexistent")

        assert result['success'] is False
        assert "not found" in result['error']

    def test_get_canonical_mappings(self, task_store):
        """Test getting all canonical mappings."""
        task_store.add_canonical_mapping("auth", "authentication")
        task_store.add_canonical_mapping("auth", "auth-api")
        task_store.add_canonical_mapping("database", "db")

        mappings = task_store.get_canonical_mappings()

        assert mappings["authentication"] == "auth"
        assert mappings["auth-api"] == "auth"
        assert mappings["db"] == "database"

    def test_get_all_canonical_tags(self, task_store):
        """Test getting canonical tags grouped."""
        task_store.add_canonical_mapping("auth", "authentication")
        task_store.add_canonical_mapping("auth", "auth-api")
        task_store.add_canonical_mapping("database", "db")

        canonical_tags = task_store.get_all_canonical_tags()

        assert len(canonical_tags) == 2

        auth_group = next((g for g in canonical_tags if g['canonical_tag'] == 'auth'), None)
        assert auth_group is not None
        assert set(auth_group['variants']) == {"authentication", "auth-api"}

        db_group = next((g for g in canonical_tags if g['canonical_tag'] == 'database'), None)
        assert db_group is not None
        assert db_group['variants'] == ["db"]


class TestTagValidation:
    """
    Tests for tag validation (special characters allowed).
    """

    def test_colon_in_tag(self, task_store):
        """Test that colon is allowed in tags."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["type:refactor", "priority:high", "domain:api"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        assert "type:refactor" in task.tags
        assert "priority:high" in task.tags
        assert "domain:api" in task.tags

    def test_space_in_tag(self, task_store):
        """Test that space is allowed in tags."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["rest api", "laravel framework", "php 8"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        assert "rest api" in task.tags
        assert "laravel framework" in task.tags
        assert "php 8" in task.tags

    def test_dot_in_tag(self, task_store):
        """Test that dot is allowed in tags."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["v2.0", "api.v1", "node.js"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        assert "v2.0" in task.tags
        assert "api.v1" in task.tags
        assert "node.js" in task.tags

    def test_mixed_special_chars(self, task_store):
        """Test mixed special characters in tags."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["api v2.0", "type:bug fix", "node-js framework"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        assert "api v2.0" in task.tags
        assert "type:bug fix" in task.tags
        assert "node-js framework" in task.tags

    def test_tags_normalized_to_lowercase(self, task_store):
        """Test that tags are normalized to lowercase."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["LARAVEL", "Type:Refactor", "PHP 8"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        assert "laravel" in task.tags
        assert "type:refactor" in task.tags
        assert "php 8" in task.tags

    def test_invalid_chars_still_filtered(self, task_store):
        """Test that truly invalid characters are filtered."""
        result = task_store.create_task(
            title="Test",
            content="Content",
            tags=["valid", "invalid!@#", "also-valid", "with$money"]
        )

        task = task_store.get_task_by_id(result['task_id'])
        assert "valid" in task.tags
        assert "also-valid" in task.tags
        assert "invalid!@#" not in task.tags
        assert "with$money" not in task.tags


class TestTagFrequencies:
    """
    Tests for tag frequencies and IDF weights.
    """

    def test_get_tag_frequencies_empty(self, task_store):
        """Test frequencies with no tasks."""
        frequencies = task_store.get_tag_frequencies()
        assert frequencies == {}

    def test_get_tag_frequencies_with_tasks(self, task_store):
        """Test frequencies calculation."""
        task_store.create_task(title="T1", content="C1", tags=["api", "backend"])
        task_store.create_task(title="T2", content="C2", tags=["api", "frontend"])
        task_store.create_task(title="T3", content="C3", tags=["backend"])

        frequencies = task_store.get_tag_frequencies()

        assert "api" in frequencies
        assert "backend" in frequencies
        assert "frontend" in frequencies
        assert frequencies["api"]["count"] == 2
        assert frequencies["backend"]["count"] == 2
        assert frequencies["frontend"]["count"] == 1

    def test_idf_weight_higher_for_rare_tags(self, task_store):
        """Test that rare tags have higher IDF weight."""
        task_store.create_task(title="T1", content="C1", tags=["common"])
        task_store.create_task(title="T2", content="C2", tags=["common"])
        task_store.create_task(title="T3", content="C3", tags=["common"])
        task_store.create_task(title="T4", content="C4", tags=["rare"])

        frequencies = task_store.get_tag_frequencies()

        assert frequencies["rare"]["idf_weight"] > frequencies["common"]["idf_weight"]

    def test_get_tag_weights(self, task_store):
        """Test simplified tag weights."""
        task_store.create_task(title="T1", content="C1", tags=["api"])
        task_store.create_task(title="T2", content="C2", tags=["rare"])

        weights = task_store.get_tag_weights()

        assert "api" in weights
        assert "rare" in weights
        assert isinstance(weights["api"], float)
        assert isinstance(weights["rare"], float)

    def test_idf_weight_formula(self, task_store):
        """Test IDF weight formula: 1 / log(1 + count)."""
        import math
        task_store.create_task(title="T1", content="C1", tags=["tag1"])

        frequencies = task_store.get_tag_frequencies()

        expected = 1.0 / math.log(1 + 1)
        assert abs(frequencies["tag1"]["idf_weight"] - expected) < 0.001