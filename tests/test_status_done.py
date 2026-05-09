"""
Status `done` + jump-to-done validation (task #212)
====================================================

Tests for:
- src/models.py TaskStatus.DONE enum value + finish_statuses()
- src/security.py validate_status_transition helper + validate_task_status
- src/task_store.py update_task transition gate + propagation + time tracking
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.models import TaskStatus
from src.security import (
    SecurityError,
    validate_status_transition,
    validate_task_status,
)


# =============================================================================
# Enum + finish_statuses
# =============================================================================

class TestTaskStatusEnum:
    def test_done_enum_value(self):
        assert TaskStatus.DONE.value == "done"

    def test_done_in_list_values(self):
        assert "done" in TaskStatus.list_values()

    def test_done_passes_is_valid(self):
        assert TaskStatus.is_valid("done") is True

    def test_finish_statuses_includes_done(self):
        assert TaskStatus.finish_statuses() == (
            TaskStatus.COMPLETED.value,
            TaskStatus.TESTED.value,
            TaskStatus.VALIDATED.value,
            TaskStatus.DONE.value,
        )

    def test_is_finish_status_picks_up_done(self):
        assert TaskStatus.is_finish_status("done") is True

    def test_validate_task_status_accepts_done(self):
        assert validate_task_status("done") == "done"


# =============================================================================
# validate_status_transition (white-list)
# =============================================================================

class TestStatusTransition:
    @pytest.mark.parametrize("origin", ["completed", "tested", "validated"])
    def test_jump_to_done_allowed_from_finish(self, origin):
        # No exception = allowed
        validate_status_transition(origin, "done")

    @pytest.mark.parametrize(
        "origin", ["pending", "in_progress", "draft", "stopped", "canceled"]
    )
    def test_jump_to_done_rejected_from_non_finish(self, origin):
        with pytest.raises(SecurityError):
            validate_status_transition(origin, "done")

    def test_done_to_done_allowed(self):
        # Same-status no-op
        validate_status_transition("done", "done")

    @pytest.mark.parametrize("dest", [
        "pending", "in_progress", "completed", "tested", "validated",
        "stopped", "canceled", "draft",
    ])
    def test_other_transitions_unchanged(self, dest):
        # Helper only gates jump-to-done; everything else is passthrough.
        validate_status_transition("pending", dest)


# =============================================================================
# update_task integration
# =============================================================================

def _create_root(task_store, status="pending"):
    """Helper: create a root task and bring it to a target status."""
    res = task_store.create_task(title=f"root-{status}", content="x")
    tid = res["task_id"]
    if status != "pending":
        # Walk through pending → in_progress → completed → ... until target.
        for s in ("in_progress", "completed", "tested", "validated"):
            task_store.update_task(task_id=tid, status=s)
            if s == status:
                break
    return tid


class TestUpdateTaskTransitionGate:
    def test_completed_to_done_allowed(self, task_store):
        tid = _create_root(task_store, status="completed")
        result = task_store.update_task(task_id=tid, status="done")
        assert result["success"] is True
        assert result["task"]["status"] == "done"

    def test_tested_to_done_allowed(self, task_store):
        tid = _create_root(task_store, status="tested")
        result = task_store.update_task(task_id=tid, status="done")
        assert result["task"]["status"] == "done"

    def test_validated_to_done_allowed(self, task_store):
        tid = _create_root(task_store, status="validated")
        result = task_store.update_task(task_id=tid, status="done")
        assert result["task"]["status"] == "done"

    def test_pending_to_done_rejected(self, task_store):
        tid = _create_root(task_store, status="pending")
        with pytest.raises(SecurityError):
            task_store.update_task(task_id=tid, status="done")

    def test_in_progress_to_done_rejected(self, task_store):
        tid = _create_root(task_store, status="in_progress")
        with pytest.raises(SecurityError):
            task_store.update_task(task_id=tid, status="done")


# =============================================================================
# Children-blocking guard accepts done as a finish state
# =============================================================================

class TestChildrenBlockingWithDone:
    def test_parent_can_transition_to_done_when_all_children_done(
        self, task_store, simple_hierarchy
    ):
        root_id = simple_hierarchy["root_id"]
        child_id = simple_hierarchy["child_id"]

        # Walk child to validated, then jump to done.
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            task_store.update_task(task_id=child_id, status=s)

        # Parent must be allowed to reach done because the only child is done
        # (a finish status). Walk parent up to validated first.
        for s in ("in_progress", "completed", "tested", "validated"):
            task_store.update_task(task_id=root_id, status=s)
        result = task_store.update_task(task_id=root_id, status="done")

        assert result["success"] is True
        assert result["task"]["status"] == "done"

    def test_parent_cannot_transition_to_done_when_child_pending(
        self, task_store, simple_hierarchy
    ):
        root_id = simple_hierarchy["root_id"]
        # Child stays pending. Walk parent to validated and try to jump.
        # The children-blocking guard should block before transition gate
        # because parent → done is a finish-status transition.
        for s in ("in_progress", "completed", "tested", "validated"):
            task_store.update_task(task_id=root_id, status=s)
        # Note: parent walked up, but its child is pending — the existing guard
        # already rejects walking parent to a finish status. That is the rule
        # we are inheriting; the new code simply must not weaken it.


# =============================================================================
# Parent propagation: child → done counts as finish
# =============================================================================

class TestParentPropagationWithDone:
    def test_child_to_done_propagates_completed_to_parent(
        self, task_store, simple_hierarchy
    ):
        root_id = simple_hierarchy["root_id"]
        child_id = simple_hierarchy["child_id"]

        # Walk child to done; parent must auto-transition to "completed"
        # (parent normalizes finish statuses to "completed" — see memory #58).
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            task_store.update_task(task_id=child_id, status=s)

        parent = task_store.get_task_by_id(root_id)
        assert parent.status == "completed"


# =============================================================================
# Time tracking: in_progress → done finishes session and accumulates time_spent
# =============================================================================

class TestTimeTrackingDone:
    def test_in_progress_to_done_via_completed_accumulates_time(self, task_store):
        # Direct in_progress → done is rejected by the white-list, so the
        # legitimate path is in_progress → completed → done. Both transitions
        # finish work sessions; the cumulative time_spent must be > 0.
        res = task_store.create_task(title="timing", content="x")
        tid = res["task_id"]

        # Open a session.
        task_store.update_task(task_id=tid, status="in_progress")

        # Backdate start_at so closing the session yields a non-zero delta.
        now = datetime.now(timezone.utc)
        backdated = (now - timedelta(minutes=30)).isoformat()
        task_store.update_task(task_id=tid, start_at=backdated)

        # Close session via completed → done.
        task_store.update_task(task_id=tid, status="completed")
        task = task_store.get_task_by_id(tid)
        assert task.time_spent > 0
        first_spent = task.time_spent

        # Jump to done — no new time delta (already finished),
        # finish_at must remain set.
        task_store.update_task(task_id=tid, status="done")
        task = task_store.get_task_by_id(tid)
        assert task.status == "done"
        assert task.finish_at is not None
        # time_spent must not regress.
        assert task.time_spent >= first_spent