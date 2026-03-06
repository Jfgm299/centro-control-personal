from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TriggerDef:
    ref_id:        str
    module_id:     str
    label:         str
    config_schema: dict
    handler_path:  str


@dataclass
class ActionDef:
    ref_id:        str
    module_id:     str
    label:         str
    config_schema: dict
    handler_path:  str


class AutomationRegistry:

    def __init__(self):
        self._triggers: dict[str, TriggerDef] = {}
        self._actions:  dict[str, ActionDef]  = {}

    def register_trigger(
        self,
        module_id:     str,
        trigger_id:    str,
        label:         str,
        config_schema: dict,
        handler:       str,
    ) -> None:
        key = f"{module_id}.{trigger_id}"
        self._triggers[key] = TriggerDef(
            ref_id=key,
            module_id=module_id,
            label=label,
            config_schema=config_schema,
            handler_path=handler,
        )

    def register_action(
        self,
        module_id:     str,
        action_id:     str,
        label:         str,
        config_schema: dict,
        handler:       str,
    ) -> None:
        key = f"{module_id}.{action_id}"
        self._actions[key] = ActionDef(
            ref_id=key,
            module_id=module_id,
            label=label,
            config_schema=config_schema,
            handler_path=handler,
        )

    def get_trigger(self, ref_id: str) -> Optional[TriggerDef]:
        return self._triggers.get(ref_id)

    def get_action(self, ref_id: str) -> Optional[ActionDef]:
        return self._actions.get(ref_id)

    def all_triggers(self) -> list[TriggerDef]:
        return list(self._triggers.values())

    def all_actions(self) -> list[ActionDef]:
        return list(self._actions.values())

    def triggers_by_module(self) -> dict[str, list[TriggerDef]]:
        result: dict[str, list[TriggerDef]] = {}
        for t in self._triggers.values():
            result.setdefault(t.module_id, []).append(t)
        return result

    def actions_by_module(self) -> dict[str, list[ActionDef]]:
        result: dict[str, list[ActionDef]] = {}
        for a in self._actions.values():
            result.setdefault(a.module_id, []).append(a)
        return result


# Singleton global — se llena al arrancar la app
registry = AutomationRegistry()