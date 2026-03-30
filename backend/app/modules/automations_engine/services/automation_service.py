from sqlalchemy.orm import Session
from typing import List
from ..models.automation import Automation
from ..schemas import AutomationCreate, AutomationUpdate, AutomationFlowUpdate
from ..exceptions import AutomationNotFoundError, AutomationNameAlreadyExistsError
from ..core.registry import registry
from ..core.graph import build_graph


class AutomationService:

    def get_all(self, db: Session, user_id: int) -> List[Automation]:
        return db.query(Automation).filter(
            Automation.user_id == user_id
        ).order_by(Automation.created_at.desc()).all()

    def get_by_id(self, automation_id: int, db: Session, user_id: int) -> Automation:
        automation = db.query(Automation).filter(
            Automation.id      == automation_id,
            Automation.user_id == user_id,
        ).first()
        if not automation:
            raise AutomationNotFoundError(automation_id)
        return automation

    def create(self, db: Session, data: AutomationCreate, user_id: int) -> Automation:
        self._validate_name_unique(db, user_id, data.name)
        flow_dict = data.flow.model_dump(by_alias=True)
        self._validate_flow(flow_dict)
        trigger_ref = data.trigger_ref or self._extract_trigger_ref(flow_dict)

        automation = Automation(
            user_id      = user_id,
            name         = data.name,
            description  = data.description,
            is_active    = data.is_active,
            flow         = flow_dict,
            trigger_type = data.trigger_type,
            trigger_ref  = trigger_ref,
        )
        db.add(automation)
        db.commit()
        db.refresh(automation)
        return automation

    def update(self, automation_id: int, db: Session, data: AutomationUpdate, user_id: int) -> Automation:
        automation = self.get_by_id(automation_id, db, user_id)
        update_data = data.model_dump(exclude_none=True)

        if "name" in update_data and update_data["name"] != automation.name:
            self._validate_name_unique(db, user_id, update_data["name"])

        for key, value in update_data.items():
            setattr(automation, key, value)

        db.commit()
        db.refresh(automation)
        return automation

    def update_flow(self, automation_id: int, db: Session, data: AutomationFlowUpdate, user_id: int) -> Automation:
        automation = self.get_by_id(automation_id, db, user_id)
        flow_dict = data.flow.model_dump(by_alias=True)
        self._validate_flow(flow_dict)

        automation.flow = flow_dict
        if data.trigger_type is not None:
            automation.trigger_type = data.trigger_type
        automation.trigger_ref = data.trigger_ref or self._extract_trigger_ref(flow_dict)

        db.commit()
        db.refresh(automation)
        return automation

    def delete(self, automation_id: int, db: Session, user_id: int) -> None:
        automation = self.get_by_id(automation_id, db, user_id)
        db.delete(automation)
        db.commit()

    def _validate_name_unique(self, db: Session, user_id: int, name: str) -> None:
        exists = db.query(Automation).filter(
            Automation.user_id == user_id,
            Automation.name    == name,
        ).first()
        if exists:
            raise AutomationNameAlreadyExistsError(name)

    def _extract_trigger_ref(self, flow: dict) -> str | None:
        """Extrae trigger_ref del nodo trigger del flow si no fue enviado explícitamente."""
        for node in flow.get("nodes", []):
            if node.get("type") == "trigger":
                return node.get("config", {}).get("trigger_id")
        return None

    def _validate_flow(self, flow: dict) -> None:
        from ..exceptions import InvalidFlowError, TriggerNotFoundInRegistryError, ActionNotFoundInRegistryError
        nodes = flow.get("nodes", [])
        edges = flow.get("edges", [])

        trigger_nodes = [n for n in nodes if n["type"] == "trigger"]
        if not trigger_nodes:
            raise InvalidFlowError("el flujo debe tener al menos un nodo trigger")
        if len(trigger_nodes) > 1:
            raise InvalidFlowError("el flujo solo puede tener un nodo trigger")

        node_ids = {n["id"] for n in nodes}

        for edge in edges:
            if edge.get("from") not in node_ids:
                raise InvalidFlowError(f"edge referencia nodo origen inexistente: {edge.get('from')}")
            if edge.get("to") not in node_ids:
                raise InvalidFlowError(f"edge referencia nodo destino inexistente: {edge.get('to')}")

        for node in nodes:
            if node["type"] == "action":
                action_id = node.get("config", {}).get("action_id")
                if action_id and not registry.get_action(action_id):
                    raise ActionNotFoundInRegistryError(action_id)
            if node["type"] == "trigger":
                trigger_id = node.get("config", {}).get("trigger_id")
                if trigger_id and not registry.get_trigger(trigger_id):
                    raise TriggerNotFoundInRegistryError(trigger_id)


automation_service = AutomationService()