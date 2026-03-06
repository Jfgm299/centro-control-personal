from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any
from ..enums import AutomationTriggerType


class FlowNode(BaseModel):
    id:     str
    type:   str
    config: dict[str, Any] = Field(default_factory=dict)
    continue_on_error: bool = False


class FlowEdge(BaseModel):
    from_node: str = Field(alias="from")
    to_node:   str = Field(alias="to")
    when:      Optional[str] = None  # "true" | "false" | None

    model_config = ConfigDict(populate_by_name=True)


class Flow(BaseModel):
    nodes: list[FlowNode] = Field(default_factory=list)
    edges: list[FlowEdge] = Field(default_factory=list)


class AutomationCreate(BaseModel):
    name:         str = Field(min_length=1, max_length=200)
    description:  Optional[str] = None
    flow:         Flow
    trigger_type: AutomationTriggerType = AutomationTriggerType.MODULE_EVENT
    trigger_ref:  Optional[str] = None
    is_active:    bool = True


class AutomationUpdate(BaseModel):
    name:        Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active:   Optional[bool] = None


class AutomationFlowUpdate(BaseModel):
    flow:         Flow
    trigger_type: Optional[AutomationTriggerType] = None
    trigger_ref:  Optional[str] = None


class AutomationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    name:         str
    description:  Optional[str]
    is_active:    bool
    flow:         dict
    trigger_type: AutomationTriggerType
    trigger_ref:  Optional[str]
    run_count:    int
    last_run_at:  Optional[datetime]
    created_at:   datetime
    updated_at:   Optional[datetime]