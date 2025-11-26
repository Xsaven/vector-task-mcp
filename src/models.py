"""
Data Models and Type Definitions
================================

Defines the core data structures used throughout the vector task system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json


class TaskStatus(Enum):
    """Task status values for task management"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STOPPED = "stopped"

    @classmethod
    def list_values(cls) -> List[str]:
        """Get list of all status values"""
        return [status.value for status in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid status"""
        return value in cls.list_values()


class Priority(Enum):
    """Task priority levels for task management"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def list_values(cls) -> List[str]:
        """Get list of all priority values"""
        return [priority.value for priority in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid priority"""
        return value in cls.list_values()


@dataclass
class Task:
    """Represents a task entry"""
    id: Optional[int] = None
    parent_id: Optional[int] = None
    status: str = TaskStatus.PENDING.value
    priority: str = Priority.MEDIUM.value
    title: str = ""
    content: str = ""
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    start_at: Optional[datetime] = None
    finish_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    tags: List[str] = None
    estimate: Optional[float] = None
    order: Optional[int] = None
    time_spent: float = 0.0

    def __post_init__(self):
        """Initialize default values"""
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "status": self.status,
            "priority": self.priority,
            "title": self.title,
            "content": self.content,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "finish_at": self.finish_at.isoformat() if self.finish_at else None,
            "content_hash": self.content_hash,
            "tags": self.tags,
            "estimate": self.estimate,
            "order": self.order,
            "time_spent": self.time_spent
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Task':
        """Create Task from database row"""
        return cls(
            id=row[0],
            parent_id=row[1] if len(row) > 1 else None,
            status=row[2] if len(row) > 2 else TaskStatus.PENDING.value,
            priority=row[3] if len(row) > 3 else Priority.MEDIUM.value,
            title=row[4] if len(row) > 4 else "",
            content=row[5] if len(row) > 5 else "",
            comment=row[6] if len(row) > 6 else None,
            tags=json.loads(row[7]) if len(row) > 7 and row[7] else [],
            created_at=datetime.fromisoformat(row[8]) if len(row) > 8 and row[8] else None,
            start_at=datetime.fromisoformat(row[9]) if len(row) > 9 and row[9] else None,
            finish_at=datetime.fromisoformat(row[10]) if len(row) > 10 and row[10] else None,
            content_hash=row[11] if len(row) > 11 else None,
            estimate=float(row[12]) if len(row) > 12 and row[12] is not None else None,
            order=int(row[13]) if len(row) > 13 and row[13] is not None else None,
            time_spent=row[14] if len(row) > 14 else 0.0
        )


@dataclass
class TaskStats:
    """Task statistics and breakdown by status"""
    total_tasks: int = 0
    by_status: Dict[str, int] = None
    pending_count: int = 0
    in_progress_count: int = 0
    completed_count: int = 0
    stopped_count: int = 0
    with_subtasks: int = 0
    by_priority: Dict[str, int] = None
    root_task_count: int = 0
    parent_task_count: int = 0
    total_estimate: float = 0.0
    total_time_spent: float = 0.0
    avg_estimate: float = 0.0
    avg_time_spent: float = 0.0
    overdue_count: int = 0
    estimate_accuracy: float = 0.0
    tag_usage: Dict[str, int] = None

    def __post_init__(self):
        """Initialize default values"""
        if self.by_status is None:
            self.by_status = {}
        if self.by_priority is None:
            self.by_priority = {}
        if self.tag_usage is None:
            self.tag_usage = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_tasks": self.total_tasks,
            "by_status": self.by_status,
            "pending_count": self.pending_count,
            "in_progress_count": self.in_progress_count,
            "completed_count": self.completed_count,
            "stopped_count": self.stopped_count,
            "with_subtasks": self.with_subtasks,
            "by_priority": self.by_priority,
            "root_task_count": self.root_task_count,
            "parent_task_count": self.parent_task_count,
            "total_estimate": self.total_estimate,
            "total_time_spent": self.total_time_spent,
            "avg_estimate": self.avg_estimate,
            "avg_time_spent": self.avg_time_spent,
            "overdue_count": self.overdue_count,
            "estimate_accuracy": self.estimate_accuracy,
            "tag_usage": self.tag_usage
        }


# Configuration constants
class Config:
    """Configuration constants"""

    # Server configuration
    SERVER_NAME = "Vector Task MCP Server"
    SERVER_VERSION = "1.0.0"

    # Content limits
    MAX_MEMORY_LENGTH = 10000  # Maximum length for content and comments (10K chars)
    MAX_TAG_LENGTH = 50        # Maximum length for single tag
    MAX_TAGS_PER_MEMORY = 10   # Maximum number of tags per task

    # Search limits
    MAX_MEMORIES_PER_SEARCH = 50  # Maximum results per search/list operation

    # Bulk operation limits
    MAX_BULK_CREATE = 50      # Maximum tasks per bulk create operation
    MAX_BULK_DELETE = 100     # Maximum task IDs per bulk delete operation

    # Database configuration
    DB_NAME = "vector_tasks.db"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384