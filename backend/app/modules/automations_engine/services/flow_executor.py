from datetime import datetime, timezone
from typing import Generator
from sqlalchemy.orm import Session
from ..core.graph import build_graph, resolve_next_nodes, Graph, Node
from ..core.node_handlers import NODE_HANDLERS
from ..core.node_handlers.stop_handler import StopExecution
from ..models.automation import Automation


class FlowExecutor:

    def execute(self, automation: Automation, payload: dict, db: Session, user_id: int) -> dict:
        ctx = {
            "payload": payload,
            "vars":    {},
            "_depth":  0,
            "user_id": user_id,
        }
        return self.execute_flow(automation.flow, ctx, db, user_id)

    def execute_flow(self, flow: dict, ctx: dict, db: Session, user_id: int) -> dict:
        graph     = build_graph(flow)
        node_logs = []

        if not graph.root:
            return {"status": "skipped", "reason": "no trigger node", "node_logs": node_logs}

        queue = [graph.root]

        while queue:
            node = queue.pop(0)
            log_entry, condition_result = self._execute_node(node, ctx, db, user_id)
            node_logs.append(log_entry)

            if log_entry["status"] == "failed" and not node.continue_on_error:
                return {"status": "failed", "error": log_entry.get("error"), "node_logs": node_logs}

            next_nodes = resolve_next_nodes(graph, node.id, condition_result)
            queue.extend(next_nodes)

        return {"status": "success", "node_logs": node_logs}

    def execute_stream(
        self,
        automation: Automation,
        payload: dict,
        db: Session,
        user_id: int,
    ) -> Generator[dict, None, None]:
        """
        Versión streaming de execute_flow.
        Hace yield de eventos por cada nodo en tiempo real:
          {"type": "node_start", "node_id": "n1"}
          {"type": "node", "node_id": "n1", "status": "success", "duration_ms": 42, "output": {...}}
          {"type": "done", "status": "success", "duration_ms": 123, "node_logs": [...]}
        """
        ctx = {
            "payload": payload,
            "vars":    {},
            "_depth":  0,
            "user_id": user_id,
        }

        graph     = build_graph(automation.flow)
        node_logs = []
        started   = datetime.now(timezone.utc)

        if not graph.root:
            yield {"type": "done", "status": "skipped", "duration_ms": 0, "node_logs": []}
            return

        queue = [graph.root]

        while queue:
            node = queue.pop(0)

            # Emitir antes de ejecutar — el frontend pone el nodo en azul
            yield {"type": "node_start", "node_id": node.id}

            log_entry, condition_result = self._execute_node(node, ctx, db, user_id)
            node_logs.append(log_entry)

            # Emitir resultado real del nodo — el frontend lo pone en verde/rojo
            yield {"type": "node", **log_entry}

            if log_entry["status"] == "failed" and not node.continue_on_error:
                break

            next_nodes = resolve_next_nodes(graph, node.id, condition_result)
            queue.extend(next_nodes)

        duration_ms  = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        final_status = "failed" if any(l["status"] == "failed" for l in node_logs) else "success"
        error        = next((l.get("error") for l in node_logs if l["status"] == "failed"), None)

        yield {
            "type":          "done",
            "status":        final_status,
            "duration_ms":   duration_ms,
            "error_message": error,
            "trigger_payload": payload,
            "node_logs":     node_logs,
        }

    def _execute_node(self, node: Node, ctx: dict, db: Session, user_id: int) -> tuple[dict, bool | None]:
        handler          = NODE_HANDLERS.get(node.type)
        start            = datetime.now(timezone.utc)
        condition_result = None

        if not handler:
            return {"node_id": node.id, "node_type": node.type, "status": "failed",
                    "error": f"Tipo de nodo desconocido: {node.type}"}, None

        try:
            result           = handler.execute(node.config, ctx, db, user_id)
            condition_result = result.get("condition_result")
            duration_ms      = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            if result:
                ctx["vars"][f"node_{node.id}"] = result

            return {
                "node_id":    node.id,
                "node_type":  node.type,
                "status":     "success",
                "output":     result,
                "duration_ms": duration_ms,
            }, condition_result

        except StopExecution as e:
            return {"node_id": node.id, "node_type": node.type,
                    "status": "skipped", "reason": e.reason}, None

        except Exception as e:
            duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            return {
                "node_id":    node.id,
                "node_type":  node.type,
                "status":     "failed",
                "error":      str(e),
                "duration_ms": duration_ms,
            }, None


flow_executor = FlowExecutor()