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

    def create_folder(self, code: str, title: str, task_id: int) -> bool:
        """Create ``{root}/{code}/`` and ``task.md`` (idempotent).

        - Folder is created with ``parents=True, exist_ok=True``.
        - If ``task.md`` does not exist → it is written from the template.
        - If it exists without a ``## Vector ID`` section → that section
          is appended via :meth:`ensure_vector_id`.
        """
        try:
            folder = self.root / code
            folder.mkdir(parents=True, exist_ok=True)

            task_md = folder / "task.md"
            if not task_md.exists():
                task_md.write_text(
                    TASK_MD_TEMPLATE.format(title=title, task_id=task_id),
                    encoding="utf-8",
                )
            else:
                self.ensure_vector_id(code, task_id)
            return True
        except Exception:
            logger.warning("create_folder failed for code=%r", code, exc_info=True)
            return False

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