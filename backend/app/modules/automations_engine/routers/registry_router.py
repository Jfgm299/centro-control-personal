from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..core.registry import registry

router = APIRouter(prefix="/automations/registry", tags=["Registry"])


@router.get("/triggers")
def get_triggers(user: User = Depends(get_current_user)):
    return [
        {
            "ref_id":        t.ref_id,
            "module_id":     t.module_id,
            "label":         t.label,
            "config_schema": t.config_schema,
        }
        for t in registry.all_triggers()
    ]


@router.get("/triggers/by-module")
def get_triggers_by_module(user: User = Depends(get_current_user)):
    return {
        module_id: [
            {"ref_id": t.ref_id, "label": t.label, "config_schema": t.config_schema}
            for t in triggers
        ]
        for module_id, triggers in registry.triggers_by_module().items()
    }


@router.get("/actions")
def get_actions(user: User = Depends(get_current_user)):
    return [
        {
            "ref_id":        a.ref_id,
            "module_id":     a.module_id,
            "label":         a.label,
            "config_schema": a.config_schema,
        }
        for a in registry.all_actions()
    ]


@router.get("/actions/by-module")
def get_actions_by_module(user: User = Depends(get_current_user)):
    return {
        module_id: [
            {"ref_id": a.ref_id, "label": a.label, "config_schema": a.config_schema}
            for a in actions
        ]
        for module_id, actions in registry.actions_by_module().items()
    }