"""
Data model for cron jobs.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class CronJob:
    """
    Model for a registered cron job.
    
    Attributes:
        id: Unique identifier for the job
        job_type: Type of job (backup, sync, clean, etc)
        schedule: Cron expression (e.g. "0 2 * * *")
        target_id: Target object ID (e.g. domain for backup)
        parameters: Possible parameters for the job
        enabled: Whether the job is currently enabled
        created_at: Time when the job was created
        last_run: Last execution time
        last_status: Status of last run (success/failure)
        description: Description of the job
    """
    job_type: str
    schedule: str
    target_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"job_{uuid.uuid4().hex[:8]}")
    enabled: bool = True
    created_at: Optional[str] = None
    last_run: Optional[str] = None
    last_status: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.created_at is None:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary."""
        return {
            "id": self.id,
            "job_type": self.job_type,
            "schedule": self.schedule,
            "target_id": self.target_id,
            "parameters": self.parameters,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "last_run": self.last_run,
            "last_status": self.last_status,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CronJob":
        """Create object from dictionary."""
        return cls(
            id=data.get("id"),
            job_type=data.get("job_type"),
            schedule=data.get("schedule"),
            target_id=data.get("target_id"),
            parameters=data.get("parameters", {}),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
            last_run=data.get("last_run"),
            last_status=data.get("last_status"),
            description=data.get("description")
        )