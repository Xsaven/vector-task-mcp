"""Task folder lifecycle manager.

Pure FS lifecycle for root-task folders: create folder + task.md, rename on
status transitions (completed/done), revert renames, recursive file listing.

Resilience contract: ALL public methods are wrapped in try/except. Failures
log a warning (with traceback) and return ``False`` (or ``None`` for
``list_files``). The manager never raises to its caller — DB operations
must always succeed regardless of filesystem state.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


TASK_MD_TEMPLATE = """# {title}

## Vector ID
{task_id}

## Branch
-

## Session ID
-

## Description
-
"""


class TaskFolderManager:
    """Pure FS lifecycle for root-task folders."""

    def __init__(self, task_folder_root: Path, working_dir: Path):
        self.root = Path(task_folder_root)
        self.working_dir = Path(working_dir)

    # ---------------------------------------------------------------- create

    # Lifecycle positions used by ensure_folder_for_status. The order
    # matches _resolve_existing_folder probe order (active first).
    _STATUSES_AT_ON_REVIEW = ("completed", "tested", "validated")
    _STATUS_AT_ARCHIVE = "done"

    def create_folder(self, code: str, title: str, task_id: int) -> bool:
        """Create or adopt the task folder (idempotent across lifecycle positions).

        Probes ``{code}/``, ``{code}-on-review/``, and ``Archive/{code}/`` in
        order — if a folder exists at ANY of those positions, it is treated
        as the canonical task folder and reused; only the ``## Vector ID``
        section is anchored. This prevents creating an empty duplicate
        ``{code}/`` when an orphan ``{code}-on-review/`` (or archived) folder
        already lives on disk from a previous session.

        When no folder exists at any position, creates ``{code}/`` with
        ``task.md`` from the default template.
        """
        try:
            existing = self._resolve_existing_folder(code)
            if existing is not None:
                # Adopt the existing folder: ensure Vector ID anchor matches
                # the current task_id at whichever position it lives.
                self._ensure_vector_id_at(existing, task_id)
                return True

            folder = self.root / code
            folder.mkdir(parents=True, exist_ok=True)

            task_md = folder / "task.md"
            if not task_md.exists():
                task_md.write_text(
                    TASK_MD_TEMPLATE.format(title=title, task_id=task_id),
                    encoding="utf-8",
                )
            else:
                self._ensure_vector_id_at(folder, task_id)
            return True
        except Exception:
            logger.warning("create_folder failed for code=%r", code, exc_info=True)
            return False

    def ensure_folder_for_status(
        self, code: str, title: str, task_id: int, status: str
    ) -> bool:
        """Ensure folder exists at the lifecycle position matching ``status``.

        - If a folder exists at ANY lifecycle position → adopt it (idempotent).
        - Else create at the position matching ``status``:
          * ``completed`` / ``tested`` / ``validated`` → ``{code}-on-review/``
          * ``done`` → ``Archive/{code}/``
          * any other (active states) → ``{code}/``

        This is the canonical entry point for creating folders in flows that
        know the task's current status (task_create, FS catch-up on init,
        legacy NULL→set in update_task). It guarantees no duplicate folders
        even when orphaned folders exist on disk from prior sessions.

        Delegates to :meth:`create_folder` (active) + :meth:`rename_on_completed`
        / :meth:`rename_on_done` rather than duplicating mkdir logic — keeps a
        single workhorse for FS creation and lets test fixtures that
        monkeypatch ``create_folder`` keep working.
        """
        try:
            # Idempotent fast-path: existing folder at any lifecycle position
            # is adopted without further FS writes.
            if self._resolve_existing_folder(code) is not None:
                # Re-anchor Vector ID on the existing position.
                self.create_folder(code, title, task_id)
                return True

            # No existing folder anywhere — create the active workhorse first.
            if not self.create_folder(code, title, task_id):
                return False

            # Move to the lifecycle position matching the supplied status.
            if status in self._STATUSES_AT_ON_REVIEW:
                return self.rename_on_completed(code)
            if status == self._STATUS_AT_ARCHIVE:
                return self.rename_on_done(code)
            return True
        except Exception:
            logger.warning(
                "ensure_folder_for_status failed for code=%r status=%r",
                code, status, exc_info=True,
            )
            return False

    def _ensure_vector_id_at(self, folder: Path, task_id: int) -> None:
        """Append ``## Vector ID`` to ``folder/task.md`` if missing.

        Path-aware variant of :meth:`ensure_vector_id` that operates on the
        already-resolved folder rather than re-deriving ``{root}/{code}``.
        Never raises — failures are logged.
        """
        try:
            task_md = folder / "task.md"
            if not task_md.exists():
                return
            content = task_md.read_text(encoding="utf-8")
            if "## Vector ID" in content:
                return
            new_content = content.rstrip() + f"\n\n## Vector ID\n{task_id}\n"
            task_md.write_text(new_content, encoding="utf-8")
        except Exception:
            logger.warning(
                "_ensure_vector_id_at failed for %s", folder, exc_info=True
            )

    def ensure_vector_id(self, code: str, task_id: int) -> None:
        """Append a ``## Vector ID`` section to ``task.md`` when missing.

        No-op if the section already exists or the file is missing.
        Never raises — failures are logged.
        """
        try:
            task_md = self.root / code / "task.md"
            if not task_md.exists():
                return
            content = task_md.read_text(encoding="utf-8")
            if "## Vector ID" in content:
                return
            new_content = content.rstrip() + f"\n\n## Vector ID\n{task_id}\n"
            task_md.write_text(new_content, encoding="utf-8")
        except Exception:
            logger.warning("ensure_vector_id failed for code=%r", code, exc_info=True)

    # ---------------------------------------------------------------- rename

    def rename_on_completed(self, code: str) -> bool:
        """Rename ``{code}`` → ``{code}-on-review`` (atomic POSIX rename)."""
        try:
            src = self.root / code
            dst = self.root / f"{code}-on-review"

            if dst.exists():
                # Already renamed — idempotent success.
                return True
            if not src.exists():
                logger.warning("rename_on_completed: source missing %s", src)
                return False
            src.rename(dst)
            return True
        except Exception:
            logger.warning(
                "rename_on_completed failed for code=%r", code, exc_info=True
            )
            return False

    def revert_on_completed(self, code: str) -> bool:
        """Reverse :meth:`rename_on_completed` (used when status reverts)."""
        try:
            src = self.root / f"{code}-on-review"
            dst = self.root / code

            if dst.exists() and not src.exists():
                # Already reverted — idempotent success.
                return True
            if not src.exists():
                logger.warning("revert_on_completed: source missing %s", src)
                return False
            if dst.exists():
                logger.warning(
                    "revert_on_completed: target %s already exists; aborting", dst
                )
                return False
            src.rename(dst)
            return True
        except Exception:
            logger.warning(
                "revert_on_completed failed for code=%r", code, exc_info=True
            )
            return False

    def rename_on_done(self, code: str) -> bool:
        """Move the task folder into ``{root}/Archive/{code}/``.

        Source resolution: prefer ``{code}-on-review`` (set by
        ``rename_on_completed``); fall back to ``{code}`` (jump-to-done
        from validated/tested without going through completed). The
        target is a single top-level ``Archive/`` directory shared by
        every archived task, so active tasks remain visually separated
        from archived ones at the root of ``--task-folder``.
        """
        try:
            src_review = self.root / f"{code}-on-review"
            src_orig = self.root / code

            if src_review.exists():
                source = src_review
            elif src_orig.exists():
                source = src_orig
            else:
                logger.warning(
                    "rename_on_done: no source folder for code=%r", code
                )
                return False

            archive_parent = self.root / "Archive"
            archive_parent.mkdir(parents=True, exist_ok=True)
            target = archive_parent / code
            if target.exists():
                logger.warning(
                    "rename_on_done: target %s already exists; aborting", target
                )
                return False

            shutil.move(str(source), str(target))
            return True
        except Exception:
            logger.warning("rename_on_done failed for code=%r", code, exc_info=True)
            return False

    def sync_folder_position(self, code: str, target_position: str) -> bool:
        """Move the existing folder for ``code`` to ``target_position``.

        ``target_position`` is one of ``"active"``, ``"on-review"``, ``"archive"``.
        No-op (returns True) if the folder is already at the correct position
        or if no folder exists at any position. Returns False on target
        collision or unexpected error.

        Used by the shared-code aggregate logic: when multiple root tasks
        share a code, the folder must reflect the LEAST advanced status
        among them (active > on-review > archive). Moving the folder up or
        down the lifecycle ladder is a single atomic rename — Archive/{code}
        ↔ {code}-on-review ↔ {code}.
        """
        try:
            current = self._resolve_existing_folder(code)
            if current is None:
                return True  # no folder to reposition

            if target_position == "active":
                target = self.root / code
            elif target_position == "on-review":
                target = self.root / f"{code}-on-review"
            elif target_position == "archive":
                target = self.root / "Archive" / code
            else:
                logger.warning(
                    "sync_folder_position: unknown target=%r for code=%r",
                    target_position, code,
                )
                return False

            if current == target:
                return True

            if target.exists():
                logger.warning(
                    "sync_folder_position: target %s already exists; aborting",
                    target,
                )
                return False

            target.parent.mkdir(parents=True, exist_ok=True)
            current.rename(target)
            return True
        except Exception:
            logger.warning(
                "sync_folder_position failed for code=%r target=%r",
                code, target_position, exc_info=True,
            )
            return False

    def rename_code(self, old_code: str, new_code: str) -> bool:
        """Rename the on-disk folder for a code change.

        Probes each of the three lifecycle positions in order (active,
        ``-on-review``, ``Archive/{code}``) and renames the first match
        to the same position under the new code. If the new-code target
        already exists at the matched position, aborts and returns False
        without touching the source.

        No-op + success when ``old_code == new_code``.
        """
        try:
            if old_code == new_code:
                return True

            candidates = [
                (self.root / old_code, self.root / new_code),
                (self.root / f"{old_code}-on-review",
                 self.root / f"{new_code}-on-review"),
                (self.root / "Archive" / old_code,
                 self.root / "Archive" / new_code),
            ]

            for src, dst in candidates:
                if src.exists() and src.is_dir():
                    if dst.exists():
                        logger.warning(
                            "rename_code: target %s already exists; aborting", dst
                        )
                        return False
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    src.rename(dst)
                    return True

            # No source folder to rename. Not an error — the task may be
            # legacy/subtask/feature-off; caller decides whether to create.
            return False
        except Exception:
            logger.warning(
                "rename_code failed for %r → %r", old_code, new_code, exc_info=True
            )
            return False

    # ----------------------------------------------------------------- read

    def list_files(self, code: str) -> Optional[List[dict]]:
        """Return a recursive list of files in the resolved task folder.

        Each entry is ``{"path": str, "relative": bool}``. ``relative`` is
        ``True`` when the folder lives inside ``working_dir`` (and ``path``
        is then relative to it); otherwise ``path`` is absolute.

        Returns ``[]`` when the folder does not exist, and ``None`` only
        on unexpected exceptions.
        """
        try:
            folder = self._resolve_existing_folder(code)
            if folder is None:
                return []

            files: List[dict] = []
            for path in sorted(folder.rglob("*")):
                if not path.is_file():
                    continue
                try:
                    rel = path.relative_to(self.working_dir)
                    files.append({"path": str(rel), "relative": True})
                except ValueError:
                    files.append({"path": str(path), "relative": False})
            return files
        except Exception:
            logger.warning("list_files failed for code=%r", code, exc_info=True)
            return None

    def _resolve_existing_folder(self, code: str) -> Optional[Path]:
        """Find the task folder under any of its possible locations.

        Probes in order: ``{code}`` (active), ``{code}-on-review``
        (completed/awaiting review), ``Archive/{code}`` (done). The
        first match wins — under normal lifecycle exactly one of these
        exists at any given time.
        """
        for candidate in (
            self.root / code,
            self.root / f"{code}-on-review",
            self.root / "Archive" / code,
        ):
            if candidate.exists() and candidate.is_dir():
                return candidate
        return None