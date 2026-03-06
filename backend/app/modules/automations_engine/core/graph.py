from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class Node:
    id:                str
    type:              str
    config:            dict[str, Any]
    continue_on_error: bool = False


@dataclass
class Edge:
    from_node: str
    to_node:   str
    when:      Optional[str] = None  # "true" | "false" | None


@dataclass
class Graph:
    nodes: dict[str, Node]          # node_id -> Node
    edges: dict[str, list[Edge]]    # from_node_id -> [Edge]
    root:  Optional[Node] = None


def build_graph(flow: dict) -> Graph:
    nodes: dict[str, Node] = {}
    for n in flow.get("nodes", []):
        nodes[n["id"]] = Node(
            id=n["id"],
            type=n["type"],
            config=n.get("config", {}),
            continue_on_error=n.get("continue_on_error", False),
        )

    edges: dict[str, list[Edge]] = {}
    for e in flow.get("edges", []):
        edge = Edge(
            from_node=e["from"],
            to_node=e["to"],
            when=e.get("when"),
        )
        edges.setdefault(e["from"], []).append(edge)

    root = next(
        (n for n in nodes.values() if n.type == "trigger"),
        None,
    )

    return Graph(nodes=nodes, edges=edges, root=root)


def resolve_next_nodes(graph: Graph, node_id: str, condition_result: Optional[bool]) -> list[Node]:
    candidates = graph.edges.get(node_id, [])
    resolved = []
    for edge in candidates:
        if edge.when is None:
            resolved.append(graph.nodes[edge.to_node])
        elif edge.when == "true"  and condition_result is True:
            resolved.append(graph.nodes[edge.to_node])
        elif edge.when == "false" and condition_result is False:
            resolved.append(graph.nodes[edge.to_node])
    return resolved