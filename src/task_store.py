"""
Task Store Module
==================

Provides SQLite-vec based task storage with vector embeddings for semantic task search.
Handles database initialization, task CRUD operations, and vector search.
"""

import sqlite3
import sqlite_vec
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .models import Task, TaskStatus, TaskStats, Config, Priority
from .security import (
    SecurityError, sanitize_input, validate_task_status,
    validate_task_params, validate_task_update_params,
    generate_content_hash, validate_file_path, validate_parent_id,
    validate_bulk_tasks_params, validate_bulk_task_ids
)
from .embeddings import get_embedding_model


class TaskStore:
    """Thread-safe task storage using sqlite-vec for semantic search."""

    def __init__(self, db_path: Path, embedding_model_name: str = None):
        """
        Initialize task store.

        Args:
            db_path: Path to SQLite database file
            embedding_model_name: Name of embedding model to use
        """
        self.db_path = Path(db_path)
        self.embedding_model_name = embedding_model_name or Config.EMBEDDING_MODEL

        # Validate database path
        validate_file_path(self.db_path)

        # Initialize database and embedding model
        self._init_database()
        self.embedding_model = get_embedding_model(self.embedding_model_name)

    def _init_database(self) -> None:
        """Initialize sqlite-vec database with required tables."""
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize task store: {e}")

        try:
            # Create tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    comment TEXT,
                    content_hash TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    start_at TEXT,
                    finish_at TEXT
                )
            """)

            # Migration: Add comment column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'comment' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN comment TEXT")

            # Migration: Add priority column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'priority' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")

            # Migration: Add tags column if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'tags' not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN tags TEXT")

            # Create vector table using vec0
            conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS task_vectors USING vec0(
                    embedding float[{Config.EMBEDDING_DIM}]
                );
            """)

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_created ON tasks(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_parent ON tasks(parent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_hash ON tasks(content_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_priority ON tasks(status, priority, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_tags ON tasks(tags)")

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to initialize database: {e}")
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection with sqlite-vec loaded."""
        conn = sqlite3.connect(str(self.db_path))
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        # Enable WAL mode for safe concurrent access
        conn.execute("PRAGMA journal_mode=WAL")
        conn.enable_load_extension(False)
        return conn

    def create_task(self, title: str, content: str, parent_id: Optional[int] = None, comment: Optional[str] = None, priority: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new task with vector embedding.

        Args:
            title: Task title
            content: Task content
            parent_id: Optional parent task ID for subtasks
            comment: Optional comment/note for the task
            priority: Optional priority level (low, medium, high, critical)
            tags: Optional list of tags for categorization

        Returns:
            Dict with operation result and task data
        """
        # Validate parameters (including comment, priority, and tags)
        title, content, _, validated_parent_id, validated_comment, validated_priority, validated_tags = validate_task_params(
            title, content, parent_id=parent_id, comment=comment, priority=priority, tags=tags
        )

        # Generate content hash from title + content (tags not included in hash)
        combined = f"{title}\n{content}\n{' '.join(validated_tags)}"
        content_hash = generate_content_hash(f"{title}\n{content}")

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to create task: {e}")

        try:
            # Check if task already exists
            existing = conn.execute(
                "SELECT id FROM tasks WHERE content_hash = ?",
                (content_hash,)
            ).fetchone()

            if existing:
                return {
                    "success": False,
                    "message": "Task already exists",
                    "task_id": existing[0]
                }

            # Generate embedding from title + content
            embedding = self.embedding_model.encode_single(combined)

            # Store task
            now = datetime.now(timezone.utc).isoformat()
            cursor = conn.execute("""
                INSERT INTO tasks (parent_id, status, title, content, comment, priority, tags, content_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (validated_parent_id, TaskStatus.PENDING.value, title, content, validated_comment, validated_priority, json.dumps(validated_tags), content_hash, now))

            task_id = cursor.lastrowid

            # Validate self-reference before committing
            validate_parent_id(task_id, validated_parent_id, conn)

            # Store vector using sqlite-vec serialization
            embedding_blob = sqlite_vec.serialize_float32(embedding)
            conn.execute(
                "INSERT INTO task_vectors (rowid, embedding) VALUES (?, ?)",
                (task_id, embedding_blob)
            )

            conn.commit()

            return {
                "success": True,
                "task_id": task_id,
                "title": title,
                "content": content,
                "comment": validated_comment,
                "priority": validated_priority,
                "tags": validated_tags,
                "status": TaskStatus.PENDING.value,
                "created_at": now
            }

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to create task: {e}")
        finally:
            conn.close()

    def create_tasks_bulk(self, tasks: List[dict]) -> Dict[str, Any]:
        """
        Create multiple tasks in a single transaction with batch embedding generation.

        Args:
            tasks: List of task dictionaries, each containing:
                - title: Task title (required)
                - content: Task content (required)
                - parent_id: Optional parent task ID
                - comment: Optional comment/note

        Returns:
            Dict with operation result:
                - success: True if all tasks created, False otherwise
                - created_task_ids: List of created task IDs
                - count: Number of tasks created
                - message: Success or error message
                - skipped: Optional list of skipped tasks (duplicates)

        Raises:
            SecurityError: If validation fails
            RuntimeError: If database operation fails
        """
        # Validate parameters
        validated_tasks, _ = validate_bulk_tasks_params(tasks, Config.MAX_BULK_CREATE)

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to create tasks: {e}")

        try:
            now = datetime.now(timezone.utc).isoformat()
            created_task_ids = []
            skipped_tasks = []
            task_insert_data = []
            combined_texts = []
            task_metadata = []

            # First pass: validate and prepare data
            for index, validated_tuple in enumerate(validated_tasks):
                title, content, _, validated_parent_id, validated_comment, validated_priority, validated_tags = validated_tuple

                # Generate content hash from title + content (tags not included)
                combined = f"{title}\n{content}\n{' '.join(validated_tags)}"
                content_hash = generate_content_hash(f"{title}\n{content}")

                # Check if task already exists
                existing = conn.execute(
                    "SELECT id FROM tasks WHERE content_hash = ?",
                    (content_hash,)
                ).fetchone()

                if existing:
                    skipped_tasks.append({
                        "index": index,
                        "task_id": existing[0],
                        "title": title[:50],
                        "reason": "Task already exists"
                    })
                    continue

                # Store metadata for later use
                task_metadata.append({
                    "title": title,
                    "content": content,
                    "parent_id": validated_parent_id,
                    "comment": validated_comment,
                    "priority": validated_priority,
                    "tags": validated_tags,
                    "content_hash": content_hash
                })

                combined_texts.append(combined)

            # If all tasks were skipped, return early
            if not task_metadata:
                return {
                    "success": True,
                    "created_task_ids": [],
                    "count": 0,
                    "message": f"No tasks created (all {len(skipped_tasks)} tasks already exist)",
                    "skipped": skipped_tasks
                }

            # Batch generate embeddings for all valid tasks
            embeddings = self.embedding_model.encode(combined_texts)

            # Second pass: insert tasks and vectors in single transaction
            for idx, metadata in enumerate(task_metadata):
                # Insert task
                cursor = conn.execute("""
                    INSERT INTO tasks (parent_id, status, title, content, comment, priority, tags, content_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata["parent_id"],
                    TaskStatus.PENDING.value,
                    metadata["title"],
                    metadata["content"],
                    metadata["comment"],
                    metadata["priority"],
                    json.dumps(metadata["tags"]),
                    metadata["content_hash"],
                    now
                ))

                task_id = cursor.lastrowid
                created_task_ids.append(task_id)

                # Validate self-reference before continuing
                validate_parent_id(task_id, metadata["parent_id"], conn)

                # Store vector using sqlite-vec serialization
                embedding_blob = sqlite_vec.serialize_float32(embeddings[idx])
                conn.execute(
                    "INSERT INTO task_vectors (rowid, embedding) VALUES (?, ?)",
                    (task_id, embedding_blob)
                )

            # Commit all operations
            conn.commit()

            result = {
                "success": True,
                "created_task_ids": created_task_ids,
                "count": len(created_task_ids),
                "message": f"Successfully created {len(created_task_ids)} task(s)"
            }

            if skipped_tasks:
                result["skipped"] = skipped_tasks
                result["message"] += f" ({len(skipped_tasks)} skipped as duplicates)"

            return result

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to create tasks in bulk: {e}")
        finally:
            conn.close()

    def update_task(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """
        Update an existing task.

        Args:
            task_id: Task ID to update
            **kwargs: Fields to update (title, content, status, parent_id, start_at, finish_at)

        Returns:
            Dict with updated task data
        """
        # Validate parameters
        task_id, validated_kwargs = validate_task_update_params(task_id, **kwargs)

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to update task: {e}")

        try:
            # Validate self-reference and parent existence if parent_id is being updated
            if 'parent_id' in validated_kwargs:
                validate_parent_id(task_id, validated_kwargs['parent_id'], conn)

            # Check if task exists
            existing = conn.execute(
                "SELECT id, title, content, status FROM tasks WHERE id = ?",
                (task_id,)
            ).fetchone()

            if not existing:
                return {
                    "success": False,
                    "message": f"Task {task_id} not found"
                }

            # Build UPDATE query dynamically
            update_fields = []
            update_values = []

            regenerate_embedding = False
            new_title = existing[1]
            new_content = existing[2]

            # Auto-set finish_at on status change to/from completed
            if 'status' in validated_kwargs:
                current_status = existing[3]  # status is 4th column (index 3)
                new_status = validated_kwargs['status']

                if new_status == 'completed' and current_status != 'completed':
                    # Completing task - set finish_at timestamp (only if not explicitly provided)
                    if 'finish_at' not in validated_kwargs:
                        validated_kwargs['finish_at'] = datetime.now(timezone.utc).isoformat()
                elif new_status != 'completed' and current_status == 'completed':
                    # Un-completing task - clear finish_at (only if not explicitly provided)
                    if 'finish_at' not in validated_kwargs:
                        validated_kwargs['finish_at'] = None

            for key, value in validated_kwargs.items():
                if key == 'title':
                    update_fields.append("title = ?")
                    update_values.append(value)
                    new_title = value
                    regenerate_embedding = True
                elif key == 'content':
                    update_fields.append("content = ?")
                    update_values.append(value)
                    new_content = value
                    regenerate_embedding = True
                elif key == 'status':
                    update_fields.append("status = ?")
                    update_values.append(value)
                elif key == 'parent_id':
                    update_fields.append("parent_id = ?")
                    update_values.append(value)
                elif key == 'start_at':
                    update_fields.append("start_at = ?")
                    update_values.append(value)
                elif key == 'finish_at':
                    update_fields.append("finish_at = ?")
                    update_values.append(value)
                elif key == 'comment':
                    update_fields.append("comment = ?")
                    update_values.append(value)
                elif key == 'priority':
                    update_fields.append("priority = ?")
                    update_values.append(value)
                elif key == 'tags':
                    update_fields.append("tags = ?")
                    update_values.append(json.dumps(value))
                    regenerate_embedding = True

            # If title, content, or tags changed, regenerate hash and embedding
            if regenerate_embedding:
                # Fetch current tags if tags not being updated
                if 'tags' not in validated_kwargs:
                    current_tags_row = conn.execute(
                        "SELECT tags FROM tasks WHERE id = ?",
                        (task_id,)
                    ).fetchone()
                    new_tags = json.loads(current_tags_row[0]) if current_tags_row[0] else []
                else:
                    new_tags = validated_kwargs['tags']

                combined = f"{new_title}\n{new_content}\n{' '.join(new_tags)}"
                new_hash = generate_content_hash(f"{new_title}\n{new_content}")
                update_fields.append("content_hash = ?")
                update_values.append(new_hash)

                # Generate new embedding
                embedding = self.embedding_model.encode_single(combined)
                embedding_blob = sqlite_vec.serialize_float32(embedding)

                # Update vector
                conn.execute(
                    "UPDATE task_vectors SET embedding = ? WHERE rowid = ?",
                    (embedding_blob, task_id)
                )

            # Execute update
            if update_fields:
                update_values.append(task_id)
                conn.execute(f"""
                    UPDATE tasks
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, update_values)

            conn.commit()

            # Fetch updated task
            result = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash
                FROM tasks
                WHERE id = ?
            """, (task_id,)).fetchone()

            task = Task.from_db_row(result)

            return {
                "success": True,
                "task": task.to_dict()
            }

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to update task: {e}")
        finally:
            conn.close()

    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task by ID.

        Args:
            task_id: Task ID to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to delete task: {e}")

        try:
            # Check if task exists
            exists = conn.execute(
                "SELECT 1 FROM tasks WHERE id = ?",
                (task_id,)
            ).fetchone()

            if not exists:
                return False

            # Delete from both tables
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.execute("DELETE FROM task_vectors WHERE rowid = ?", (task_id,))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to delete task: {e}")
        finally:
            conn.close()

    def delete_tasks_bulk(self, task_ids: List[int]) -> Dict[str, Any]:
        """
        Delete multiple tasks in a single transaction.

        Args:
            task_ids: List of task IDs to delete

        Returns:
            Dict with operation result:
                - success: True if all found tasks deleted, False otherwise
                - deleted_count: Number of tasks deleted
                - deleted_task_ids: List of deleted task IDs
                - message: Success or error message
                - not_found: Optional list of task IDs not found

        Raises:
            SecurityError: If validation fails
            RuntimeError: If database operation fails
        """
        # Validate and deduplicate task IDs
        deduplicated_task_ids = validate_bulk_task_ids(task_ids, Config.MAX_BULK_DELETE)

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to delete tasks: {e}")

        try:
            # Check which tasks exist
            placeholders = ','.join('?' * len(deduplicated_task_ids))
            existing_ids_query = f"SELECT id FROM tasks WHERE id IN ({placeholders})"
            existing_rows = conn.execute(existing_ids_query, deduplicated_task_ids).fetchall()
            existing_ids = [row[0] for row in existing_rows]

            # Determine which IDs were not found
            not_found_ids = [task_id for task_id in deduplicated_task_ids if task_id not in existing_ids]

            # If no tasks exist, return early
            if not existing_ids:
                return {
                    "success": False,
                    "deleted_count": 0,
                    "deleted_task_ids": [],
                    "message": f"No tasks found to delete (0 of {len(deduplicated_task_ids)})",
                    "not_found": not_found_ids
                }

            # Delete from both tables in single transaction
            delete_placeholders = ','.join('?' * len(existing_ids))

            conn.execute(
                f"DELETE FROM tasks WHERE id IN ({delete_placeholders})",
                existing_ids
            )

            conn.execute(
                f"DELETE FROM task_vectors WHERE rowid IN ({delete_placeholders})",
                existing_ids
            )

            conn.commit()

            result = {
                "success": True,
                "deleted_count": len(existing_ids),
                "deleted_task_ids": existing_ids,
                "message": f"Successfully deleted {len(existing_ids)} task(s)"
            }

            if not_found_ids:
                result["not_found"] = not_found_ids
                result["message"] += f" ({len(not_found_ids)} not found)"

            return result

        except SecurityError as e:
            conn.rollback()
            raise e
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to delete tasks in bulk: {e}")
        finally:
            conn.close()

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Task object or None if not found
        """
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get task: {e}")

        try:
            result = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash
                FROM tasks
                WHERE id = ?
            """, (task_id,)).fetchone()

            if result:
                return Task.from_db_row(result)
            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get task by ID: {e}")
        finally:
            conn.close()

    def get_last_task(self) -> Optional[Task]:
        """
        Get the most recently created task.

        Returns:
            Task object or None if no tasks exist
        """
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get last task: {e}")

        try:
            result = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash
                FROM tasks
                ORDER BY created_at DESC
                LIMIT 1
            """).fetchone()

            if result:
                return Task.from_db_row(result)
            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get last task: {e}")
        finally:
            conn.close()

    def get_next_task(self) -> Optional[Task]:
        """
        Get the next task to work on.

        Logic:
        1. First check: any tasks with status="in_progress" → return first one
        2. If none in_progress: find last completed task, then return first pending task created after it
        3. If no completed: return first pending task by created_at

        Returns:
            Task object or None if no suitable task found
        """
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get next task: {e}")

        try:
            # First check for in_progress tasks
            in_progress = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash
                FROM tasks
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT 1
            """, (TaskStatus.IN_PROGRESS.value,)).fetchone()

            if in_progress:
                return Task.from_db_row(in_progress)

            # Find last completed task
            last_completed = conn.execute("""
                SELECT created_at
                FROM tasks
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (TaskStatus.COMPLETED.value,)).fetchone()

            if last_completed:
                # Get first pending task created after last completed
                next_pending = conn.execute("""
                    SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash
                    FROM tasks
                    WHERE status = ? AND created_at > ?
                    ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, created_at ASC
                    LIMIT 1
                """, (TaskStatus.PENDING.value, last_completed[0])).fetchone()

                if next_pending:
                    return Task.from_db_row(next_pending)

            # No completed tasks or no pending after completed, get first pending
            first_pending = conn.execute("""
                SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash
                FROM tasks
                WHERE status = ?
                ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END, created_at ASC
                LIMIT 1
            """, (TaskStatus.PENDING.value,)).fetchone()

            if first_pending:
                return Task.from_db_row(first_pending)

            return None

        except Exception as e:
            raise RuntimeError(f"Failed to get next task: {e}")
        finally:
            conn.close()

    def search_tasks(
        self,
        query: str = None,
        limit: int = 10,
        offset: int = 0,
        status: str = None,
        parent_id: int = None,
        tags: List[str] = None
    ) -> Tuple[List[Task], int]:
        """
        Search tasks using vector similarity or list all with filters.

        Args:
            query: Optional search query for semantic search
            limit: Maximum number of results
            offset: Number of results to skip for pagination
            status: Optional status filter
            parent_id: Optional parent_id filter
            tags: Optional list of tags to filter by (OR logic - matches if ANY tag present)

        Returns:
            Tuple of (List of Task objects, total count matching filters)
        """
        # Validate parameters
        if limit is not None:
            limit = min(max(1, limit), Config.MAX_MEMORIES_PER_SEARCH)
        else:
            limit = 10

        if offset is not None and (not isinstance(offset, int) or offset < 0):
            raise ValueError("offset must be a non-negative integer")
        if offset and offset > 10000:
            raise ValueError("offset must not exceed 10000")

        if status is not None:
            status = validate_task_status(status)

        if parent_id is not None and not isinstance(parent_id, int):
            raise ValueError("parent_id must be an integer")

        # Validate tags (optional)
        validated_tags = None
        if tags is not None:
            if not isinstance(tags, list):
                raise ValueError("tags must be a list")
            # Sanitize tags using existing sanitize_input
            validated_tags = []
            for tag in tags:
                if isinstance(tag, str) and tag.strip():
                    validated_tags.append(sanitize_input(tag.lower().strip(), 100))
            if not validated_tags:
                validated_tags = None  # Empty list = no filter

        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to search tasks: {e}")

        try:
            # If query provided, do vector search
            if query:
                query = sanitize_input(query)

                # Generate query embedding
                query_embedding = self.embedding_model.encode_single(query)
                query_blob = sqlite_vec.serialize_float32(query_embedding)

                # Build search query
                base_query = """
                    SELECT
                        t.id, t.parent_id, t.status, t.priority, t.title, t.content, t.comment, t.tags, t.created_at, t.start_at, t.finish_at, t.content_hash,
                        vec_distance_cosine(v.embedding, ?) as distance
                    FROM tasks t
                    JOIN task_vectors v ON t.id = v.rowid
                """

                params = [query_blob]
                where_clauses = []

                # Add filters
                if status:
                    where_clauses.append("t.status = ?")
                    params.append(status)

                if parent_id is not None:
                    where_clauses.append("t.parent_id = ?")
                    params.append(parent_id)

                # Add tags filter if provided (OR logic - match ANY tag)
                if validated_tags:
                    tag_conditions = " OR ".join(["EXISTS (SELECT 1 FROM json_each(t.tags) WHERE value = ?)" for _ in validated_tags])
                    where_clauses.append(f"({tag_conditions})")
                    for tag in validated_tags:
                        params.append(tag)

                # Add WHERE clause if filters exist
                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)

                # Get total count
                count_query = """
                    SELECT COUNT(DISTINCT t.id)
                    FROM tasks t
                    JOIN task_vectors v ON t.id = v.rowid
                """
                if where_clauses:
                    count_query += " WHERE " + " AND ".join(where_clauses)

                count_params = params[1:] if len(params) > 1 else []
                total_count = conn.execute(count_query, count_params).fetchone()[0]

                # Add ORDER BY, LIMIT, and OFFSET
                base_query += " ORDER BY distance LIMIT ? OFFSET ?"
                params.append(limit)
                params.append(offset)

                results = conn.execute(base_query, params).fetchall()

            else:
                # No query, just list with filters
                base_query = """
                    SELECT id, parent_id, status, priority, title, content, comment, tags, created_at, start_at, finish_at, content_hash
                    FROM tasks
                """

                params = []
                where_clauses = []

                if status:
                    where_clauses.append("status = ?")
                    params.append(status)

                if parent_id is not None:
                    where_clauses.append("parent_id = ?")
                    params.append(parent_id)

                # Add tags filter if provided (OR logic - match ANY tag)
                if validated_tags:
                    tag_conditions = " OR ".join(["EXISTS (SELECT 1 FROM json_each(tags) WHERE value = ?)" for _ in validated_tags])
                    where_clauses.append(f"({tag_conditions})")
                    for tag in validated_tags:
                        params.append(tag)

                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)

                # Get total count
                count_query = "SELECT COUNT(*) FROM tasks"
                if where_clauses:
                    count_query += " WHERE " + " AND ".join(where_clauses)

                total_count = conn.execute(count_query, params).fetchone()[0]

                # Add ORDER BY, LIMIT, and OFFSET
                base_query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.append(limit)
                params.append(offset)

                results = conn.execute(base_query, params).fetchall()

            # Format results
            tasks = []
            for row in results:
                # Exclude distance column if present (vector search)
                task_row = row[:-1] if query else row
                tasks.append(Task.from_db_row(task_row))

            return (tasks, total_count)

        except SecurityError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"Failed to search tasks: {e}")
        finally:
            conn.close()

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags across all tasks.

        Returns:
            List[str]: Sorted list of unique tags
        """
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get tags: {e}")

        try:
            # Get all non-null tags from database
            results = conn.execute("""
                SELECT tags
                FROM tasks
                WHERE tags IS NOT NULL AND tags != '[]'
            """).fetchall()

            # Parse JSON arrays and collect unique tags
            unique_tags = set()
            for row in results:
                if row[0]:
                    try:
                        tags_list = json.loads(row[0])
                        if isinstance(tags_list, list):
                            unique_tags.update(tags_list)
                    except (json.JSONDecodeError, TypeError):
                        continue

            # Return sorted list
            return sorted(list(unique_tags))

        except Exception as e:
            raise RuntimeError(f"Failed to get unique tags: {e}")
        finally:
            conn.close()

    def get_stats(self) -> TaskStats:
        """
        Get task statistics.

        Returns:
            TaskStats object with comprehensive statistics
        """
        try:
            conn = self._get_connection()
        except Exception as e:
            raise RuntimeError(f"Failed to get stats: {e}")

        try:
            # Total tasks
            total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

            # Count by status
            status_counts = dict(conn.execute("""
                SELECT status, COUNT(*)
                FROM tasks
                GROUP BY status
            """).fetchall())

            # Count tasks with subtasks (tasks that are parents)
            with_subtasks = conn.execute("""
                SELECT COUNT(DISTINCT parent_id)
                FROM tasks
                WHERE parent_id IS NOT NULL
            """).fetchone()[0]

            stats = TaskStats(
                total_tasks=total_tasks,
                by_status=status_counts,
                pending_count=status_counts.get(TaskStatus.PENDING.value, 0),
                in_progress_count=status_counts.get(TaskStatus.IN_PROGRESS.value, 0),
                completed_count=status_counts.get(TaskStatus.COMPLETED.value, 0),
                stopped_count=status_counts.get(TaskStatus.STOPPED.value, 0),
                with_subtasks=with_subtasks
            )

            return stats

        except Exception as e:
            raise RuntimeError(f"Failed to get statistics: {e}")
        finally:
            conn.close()