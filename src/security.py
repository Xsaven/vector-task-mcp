"""
Security Utilities
==================

Provides security validation, input sanitization, and path validation
for the vector memory MCP server.
"""

import re
import os
import sqlite3
from pathlib import Path
from typing import List

from .models import Config, TaskStatus, Priority


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


def validate_working_dir(working_dir: str) -> Path:
    """
    Validate and normalize working directory path.
    
    Args:
        working_dir: Directory path to validate
        
    Returns:
        Path: Validated memory directory path
        
    Raises:
        SecurityError: If validation fails
    """
    try:
        # Normalize path
        path = Path(working_dir).resolve()
        
        # Security checks
        path_str = str(path)
        if re.search(r'[;&|`$]', path_str):
            raise SecurityError("Invalid characters in path")
        
        # Check for null bytes/control chars
        if re.search(r'[\x00-\x1F\x7F]', path_str):
            raise SecurityError("Control characters in path")
        
        # Ensure directory exists or can be created
        path.mkdir(parents=True, exist_ok=True)

        # Note: Memory subdirectory will be created by caller
        # Validation function should return validated project path only
        return path
        
    except PermissionError as e:
        raise SecurityError(f"Permission denied: {e}")
    except OSError as e:
        raise SecurityError(f"Invalid path: {e}")
    except Exception as e:
        raise SecurityError(f"Path validation failed: {e}")


def sanitize_input(text: str, max_length: int = None) -> str:
    """
    Sanitize and validate user input.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length (defaults to Config.MAX_MEMORY_LENGTH)
        
    Returns:
        str: Sanitized text
        
    Raises:
        SecurityError: If validation fails
    """
    if max_length is None:
        max_length = Config.MAX_MEMORY_LENGTH
        
    if not isinstance(text, str):
        raise SecurityError("Input must be a string")
    
    # Remove null bytes and control characters (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Basic validation
    if not text.strip():
        raise SecurityError("Input cannot be empty")
    
    return text.strip()


def validate_tags(tags: List[str]) -> List[str]:
    """
    Validate and sanitize tags.
    
    Args:
        tags: List of tag strings
        
    Returns:
        List[str]: Validated and sanitized tags
        
    Raises:
        SecurityError: If validation fails
    """
    if not isinstance(tags, list):
        raise SecurityError("Tags must be a list")
    
    validated_tags = []
    for tag in tags[:Config.MAX_TAGS_PER_MEMORY]:  # Limit number of tags
        if isinstance(tag, str):
            try:
                clean_tag = sanitize_input(tag, Config.MAX_TAG_LENGTH).lower()
                # Additional tag validation
                if re.match(r'^[a-z0-9\-_]+$', clean_tag):
                    if clean_tag and clean_tag not in validated_tags:
                        validated_tags.append(clean_tag)
                else:
                    # Skip invalid tags rather than failing
                    continue
            except SecurityError:
                # Skip invalid tags rather than failing
                continue
    
    return validated_tags


def validate_category(category: str) -> str:
    """
    Validate memory category.
    
    Args:
        category: Category string to validate
        
    Returns:
        str: Validated category or "other" as fallback
    """
    if not isinstance(category, str):
        return "other"
    
    category = category.lower().strip()
    if category in Config.MEMORY_CATEGORIES:
        return category
    else:
        return "other"


def validate_comment(comment: str) -> str:
    """
    Validate and sanitize task comment.

    Args:
        comment: Comment string to validate

    Returns:
        Optional[str]: Sanitized comment or None if empty/invalid
    """
    if not isinstance(comment, str):
        return None

    # Sanitize using existing sanitize_input function
    # Max length: Config.MAX_MEMORY_LENGTH (10,000 chars - same as content)
    try:
        sanitized = sanitize_input(comment, max_length=Config.MAX_MEMORY_LENGTH)
        return sanitized
    except SecurityError:
        # If validation fails, return None (comment is optional)
        return None


def validate_search_params(query: str, limit: int, category: str = None) -> tuple:
    """
    Validate search parameters.

    Args:
        query: Search query string
        limit: Maximum results limit
        category: Optional category filter

    Returns:
        tuple: (sanitized_query, validated_limit, validated_category)

    Raises:
        SecurityError: If validation fails
    """
    # Validate query
    if not isinstance(query, str) or not query.strip():
        raise SecurityError("Search query cannot be empty")

    sanitized_query = sanitize_input(query, 1000)  # Reasonable query length

    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        limit = 10
    limit = min(limit, Config.MAX_MEMORIES_PER_SEARCH)

    # Validate category
    validated_category = None
    if category is not None:
        validated_category = validate_category(category)
        if validated_category == "other" and category != "other":
            validated_category = None  # Invalid category, ignore filter

    return sanitized_query, limit, validated_category


def validate_cleanup_params(days_old: int, max_to_keep: int) -> tuple:
    """
    Validate cleanup parameters.
    
    Args:
        days_old: Minimum age in days for cleanup candidates
        max_to_keep: Maximum total memories to keep
        
    Returns:
        tuple: (validated_days_old, validated_max_to_keep)
        
    Raises:
        SecurityError: If validation fails
    """
    if not isinstance(days_old, int) or days_old < 1:
        raise SecurityError("days_old must be a positive integer")
    
    if not isinstance(max_to_keep, int) or max_to_keep < 100:
        raise SecurityError("max_to_keep must be at least 100")
    
    # Reasonable limits
    days_old = min(days_old, 365)  # Max 1 year
    max_to_keep = min(max_to_keep, Config.MAX_TOTAL_MEMORIES)
    
    return days_old, max_to_keep


def generate_content_hash(content: str) -> str:
    """
    Generate hash for content deduplication.
    
    Args:
        content: Content to hash
        
    Returns:
        str: Content hash (16 characters)
    """
    import hashlib
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def check_resource_limits(current_count: int) -> None:
    """
    Check if resource limits would be exceeded.

    Args:
        current_count: Current number of memories in database

    Raises:
        SecurityError: If limits would be exceeded
    """
    if current_count >= Config.MAX_TOTAL_MEMORIES:
        raise SecurityError(
            f"Memory limit reached ({Config.MAX_TOTAL_MEMORIES}). "
            "Use clear_old_memories to free space."
        )


def validate_task_status(status: str) -> str:
    """
    Validate task status value.

    Args:
        status: Status string to validate

    Returns:
        str: Validated status or "pending" as fallback
    """
    if not isinstance(status, str):
        return "pending"

    status = status.lower().strip()
    if status in TaskStatus.list_values():
        return status
    else:
        return "pending"


def validate_priority(priority: str) -> str:
    """
    Validate task priority value.

    Args:
        priority: Priority string to validate

    Returns:
        str: Validated priority or "medium" as fallback
    """
    if not isinstance(priority, str):
        return "medium"

    priority = priority.lower().strip()
    if priority in Priority.list_values():
        return priority
    else:
        return "medium"


def validate_task_params(title: str, content: str, status: str = None, parent_id: int = None, comment: str = None, priority: str = None, tags: List[str] = None) -> tuple:
    """
    Validate task creation/update parameters.

    Args:
        title: Task title
        content: Task content
        status: Optional task status
        parent_id: Optional parent task ID
        comment: Optional task comment
        priority: Optional task priority
        tags: Optional list of tags

    Returns:
        tuple: (sanitized_title, sanitized_content, validated_status, validated_parent_id, validated_comment, validated_priority, validated_tags)

    Raises:
        SecurityError: If validation fails
    """
    # Validate and sanitize title
    if not isinstance(title, str) or not title.strip():
        raise SecurityError("Task title cannot be empty")

    # Check title length before sanitization
    if len(title) > 200:
        raise SecurityError(f"Task title exceeds maximum length of 200 characters (current: {len(title)})")

    sanitized_title = sanitize_input(title, 200)

    # Validate and sanitize content
    if not isinstance(content, str) or not content.strip():
        raise SecurityError("Task content cannot be empty")

    sanitized_content = sanitize_input(content, Config.MAX_MEMORY_LENGTH)

    # Validate status
    validated_status = "pending"
    if status is not None:
        validated_status = validate_task_status(status)

    # Validate parent_id
    validated_parent_id = None
    if parent_id is not None:
        if not isinstance(parent_id, int) or parent_id < 1:
            raise SecurityError("parent_id must be a positive integer")
        validated_parent_id = parent_id

    # Validate comment
    validated_comment = None
    if comment is not None:
        validated_comment = validate_comment(comment)

    # Validate priority
    validated_priority = "medium"
    if priority is not None:
        validated_priority = validate_priority(priority)

    # Validate tags
    validated_tags = []
    if tags is not None:
        validated_tags = validate_tags(tags)

    return sanitized_title, sanitized_content, validated_status, validated_parent_id, validated_comment, validated_priority, validated_tags


def validate_task_update_params(task_id: int, **kwargs) -> tuple:
    """
    Validate task update parameters.

    Args:
        task_id: Task ID to update
        **kwargs: Fields to update (title, content, status, parent_id, comment, priority, start_at, finish_at)

    Returns:
        tuple: (task_id, validated_kwargs_dict)

    Raises:
        SecurityError: If validation fails
    """
    # Validate task_id
    if not isinstance(task_id, int) or task_id < 1:
        raise SecurityError("task_id must be a positive integer")

    validated_kwargs = {}

    # Validate title if provided
    if 'title' in kwargs:
        title = kwargs['title']
        if not isinstance(title, str) or not title.strip():
            raise SecurityError("Task title cannot be empty")
        validated_kwargs['title'] = sanitize_input(title, 200)

    # Validate content if provided
    if 'content' in kwargs:
        content = kwargs['content']
        if not isinstance(content, str) or not content.strip():
            raise SecurityError("Task content cannot be empty")
        validated_kwargs['content'] = sanitize_input(content, Config.MAX_MEMORY_LENGTH)

    # Validate status if provided
    if 'status' in kwargs:
        status_value = kwargs['status']
        if not isinstance(status_value, str):
            raise SecurityError("status must be one of: pending, in_progress, completed, stopped")
        if not TaskStatus.is_valid(status_value):
            raise SecurityError("status must be one of: pending, in_progress, completed, stopped")
        validated_kwargs['status'] = status_value

    # Validate parent_id if provided
    if 'parent_id' in kwargs:
        parent_id = kwargs['parent_id']
        if parent_id is not None:
            if not isinstance(parent_id, int) or parent_id < 1:
                raise SecurityError("parent_id must be a positive integer")
        validated_kwargs['parent_id'] = parent_id

    # Validate comment if provided
    if 'comment' in kwargs:
        validated_kwargs['comment'] = validate_comment(kwargs['comment'])

    # Validate priority if provided
    if 'priority' in kwargs:
        priority_value = kwargs['priority']
        if not isinstance(priority_value, str):
            raise SecurityError("priority must be one of: low, medium, high, critical")
        if not Priority.is_valid(priority_value):
            raise SecurityError("priority must be one of: low, medium, high, critical")
        validated_kwargs['priority'] = priority_value

    # Validate tags if provided
    if 'tags' in kwargs:
        tags_value = kwargs['tags']
        if tags_value is not None:
            if not isinstance(tags_value, list):
                raise SecurityError("tags must be a list")
            validated_kwargs['tags'] = validate_tags(tags_value)
        else:
            validated_kwargs['tags'] = []  # Explicit None = clear tags

    # Validate start_at if provided (pass through - already validated as ISO8601 string)
    if 'start_at' in kwargs:
        validated_kwargs['start_at'] = kwargs['start_at']

    # Validate finish_at if provided (pass through - already validated as ISO8601 string)
    if 'finish_at' in kwargs:
        validated_kwargs['finish_at'] = kwargs['finish_at']

    return task_id, validated_kwargs


def validate_parent_id(task_id: int, parent_id: int | None, conn: sqlite3.Connection) -> None:
    """
    Validate parent_id to prevent self-reference and ensure parent exists.

    Args:
        task_id: Current task ID
        parent_id: Parent task ID to validate (can be None)
        conn: SQLite database connection

    Raises:
        SecurityError: If parent_id equals task_id (self-reference) or parent does not exist
    """
    if parent_id is None:
        return

    if parent_id == task_id:
        raise SecurityError("Task cannot be its own parent (self-reference not allowed)")

    # Check if parent task exists in database
    result = conn.execute(
        "SELECT id FROM tasks WHERE id = ?",
        (parent_id,)
    ).fetchone()

    if not result:
        raise SecurityError(f"Parent task with ID {parent_id} does not exist")


def validate_task_list_params(limit: int, offset: int, status: str = None, parent_id: int = None, tags: List[str] = None) -> tuple:
    """
    Validate task_list parameters.

    Args:
        limit: Maximum results limit
        offset: Starting position for pagination
        status: Optional status filter
        parent_id: Optional parent task ID filter
        tags: Optional list of tags to filter by

    Returns:
        tuple: (validated_limit, validated_offset, validated_status, validated_parent_id, validated_tags)

    Raises:
        SecurityError: If validation fails
    """
    # Validate limit
    if not isinstance(limit, int) or limit < 1:
        raise SecurityError("limit must be a positive integer (minimum 1)")
    limit = min(limit, Config.MAX_MEMORIES_PER_SEARCH)

    # Validate offset
    if not isinstance(offset, int) or offset < 0:
        raise SecurityError("offset must be a non-negative integer")
    offset = min(offset, 10000)

    # Validate status (optional)
    validated_status = None
    if status is not None:
        if not isinstance(status, str):
            raise SecurityError("status must be one of: pending, in_progress, completed, stopped")
        if not TaskStatus.is_valid(status):
            raise SecurityError("status must be one of: pending, in_progress, completed, stopped")
        validated_status = status

    # Validate parent_id (optional)
    validated_parent_id = None
    if parent_id is not None:
        if not isinstance(parent_id, int) or parent_id < 1:
            raise SecurityError("parent_id must be a positive integer")
        validated_parent_id = parent_id

    # Validate tags (optional)
    validated_tags = None
    if tags is not None:
        if not isinstance(tags, list):
            raise SecurityError("tags must be a list")
        validated_tags = validate_tags(tags)
        if not validated_tags:
            validated_tags = None  # Empty list after validation = no filter

    return limit, offset, validated_status, validated_parent_id, validated_tags


def validate_bulk_tasks_params(tasks: List[dict], max_batch_size: int = 50) -> tuple:
    """
    Validate bulk task creation parameters.

    Args:
        tasks: List of task dictionaries, each containing title, content, and optional status/parent_id/comment
        max_batch_size: Maximum allowed batch size (default: 50, Config.MAX_BULK_CREATE)

    Returns:
        tuple: (validated_tasks, errors) where validated_tasks is List[tuple] and errors is List[dict]

    Raises:
        SecurityError: If validation fails for any task (fail-fast with detailed error reporting)
    """
    # Validate list is not empty
    if not isinstance(tasks, list):
        raise SecurityError("tasks must be a list")

    if not tasks:
        raise SecurityError("tasks list cannot be empty")

    # Validate batch size
    if len(tasks) > max_batch_size:
        raise SecurityError(f"Batch size exceeds maximum allowed ({max_batch_size}). Current: {len(tasks)}")

    # Validate each task
    validated_tasks = []
    errors = []

    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append({
                "index": index,
                "error": "Task must be a dictionary",
                "task_data": str(task)[:100]  # Truncate for safety
            })
            continue

        try:
            # Extract task fields
            title = task.get('title')
            content = task.get('content')
            status = task.get('status')
            parent_id = task.get('parent_id')
            comment = task.get('comment')
            priority = task.get('priority')
            tags = task.get('tags')

            # Validate using existing single-task validator
            validated_tuple = validate_task_params(
                title=title,
                content=content,
                status=status,
                parent_id=parent_id,
                comment=comment,
                priority=priority,
                tags=tags
            )
            validated_tasks.append(validated_tuple)

        except SecurityError as e:
            errors.append({
                "index": index,
                "error": str(e),
                "task_data": {
                    "title": task.get('title', '')[:50] if isinstance(task.get('title'), str) else None,
                    "content": task.get('content', '')[:50] if isinstance(task.get('content'), str) else None
                }
            })

    # Fail-fast: if any errors occurred, raise with all errors
    if errors:
        error_summary = f"Validation failed for {len(errors)} task(s) out of {len(tasks)}"
        error_details = "\n".join([
            f"Task {err['index']}: {err['error']}"
            for err in errors
        ])
        raise SecurityError(f"{error_summary}\n{error_details}")

    return validated_tasks, errors


def validate_bulk_task_ids(task_ids: List[int], max_batch_size: int = 100) -> List[int]:
    """
    Validate bulk task ID list for deletion operations.

    Args:
        task_ids: List of task IDs to validate
        max_batch_size: Maximum allowed batch size (default: 100, Config.MAX_BULK_DELETE)

    Returns:
        List[int]: Deduplicated task IDs (order preserved)

    Raises:
        SecurityError: If validation fails
    """
    # Validate list is not empty
    if not isinstance(task_ids, list):
        raise SecurityError("task_ids must be a list")

    if not task_ids:
        raise SecurityError("task_ids list cannot be empty")

    # Validate batch size
    if len(task_ids) > max_batch_size:
        raise SecurityError(f"Batch size exceeds maximum allowed ({max_batch_size}). Current: {len(task_ids)}")

    # Validate each ID
    validated_ids = []
    invalid_ids = []

    for task_id in task_ids:
        if not isinstance(task_id, int):
            invalid_ids.append(f"'{task_id}' (not an integer)")
            continue

        if task_id < 1:
            invalid_ids.append(f"{task_id} (must be positive)")
            continue

        validated_ids.append(task_id)

    # Raise if any invalid IDs found
    if invalid_ids:
        raise SecurityError(
            f"Invalid task IDs found: {', '.join(invalid_ids[:5])}"
            + (f" and {len(invalid_ids) - 5} more..." if len(invalid_ids) > 5 else "")
        )

    # Deduplicate IDs (preserve order)
    deduplicated_ids = []
    seen = set()
    for task_id in validated_ids:
        if task_id not in seen:
            deduplicated_ids.append(task_id)
            seen.add(task_id)

    return deduplicated_ids


def validate_file_path(file_path: Path) -> None:
    """
    Validate database file path for security.

    Args:
        file_path: Path to validate

    Raises:
        SecurityError: If path is unsafe
    """
    # Check file extension
    if file_path.suffix != '.db':
        raise SecurityError("Database file must have .db extension")

    # Check path components for directory traversal
    for part in file_path.parts:
        # Block parent directory traversal
        if '..' in part:
            raise SecurityError("Path traversal attempt detected")
        # Block hidden files in filename (last component), but allow hidden directories
        if part == file_path.name and part.startswith('.'):
            raise SecurityError("Hidden database files not allowed")

    # Check parent directory exists and is writable
    parent = file_path.parent
    if not parent.exists():
        raise SecurityError("Parent directory does not exist")

    if not os.access(parent, os.W_OK):
        raise SecurityError("Parent directory is not writable")
