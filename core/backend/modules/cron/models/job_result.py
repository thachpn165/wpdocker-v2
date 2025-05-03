"""
Data model for cron job execution results.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class JobResult:
    """
    Result of a cron job execution.
    
    Attributes:
        job_id: ID of the job
        status: Status (success, failure, running, etc)
        start_time: Start time
        end_time: End time
        details: Additional result details
        logs: Execution log
        error: Error information (if any)
    """
    job_id: str
    status: str
    start_time: str
    details: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    end_time: Optional[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.start_time:
            self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def complete(self, status: str = "success", error: Optional[str] = None):
        """Mark the job as completed."""
        self.status = status
        self.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.error = error
    
    def add_log(self, message: str):
        """Add a log entry."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "details": self.details,
            "logs": self.logs,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobResult":
        """Create object from dictionary."""
        return cls(
            job_id=data.get("job_id"),
            status=data.get("status"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            details=data.get("details", {}),
            logs=data.get("logs", []),
            error=data.get("error")
        )