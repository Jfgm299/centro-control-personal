from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any
from ..enums import ExecutionStatus


class NodeLogEntry(BaseModel):
    node_id:          str
    node_type:        str
    status:           str
    output:           Optional[dict[str, Any]] = None
    error:            Optional[str] = None
    duration_ms:      Optional[int] = None


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    automation_id:   int
    trigger_payload: Optional[dict[str, Any]]
    status:          ExecutionStatus
    started_at:      datetime
    finished_at:     Optional[datetime]
    duration_ms:     Optional[int]
    error_message:   Optional[str]
    node_logs:       Optional[list[NodeLogEntry]] = None


class ExecutionTriggerRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)