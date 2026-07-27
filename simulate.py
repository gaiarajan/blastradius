from sparql_client import fetch_graph  
from importers.base import normalize_name
import collections


def _build_reverse_adjacency(edges: list[dict]) -> dict[str, list[tuple[str, float]]]:
    ans = {}
    for edge in edges:
        source = normalize_name(edge["source"])
        target = normalize_name(edge["target"])
        ans.setdefault(target, []).append((source, float(edge["impactWeight"])))
    return ans


def run_simulation(start_node: str, edges: list[dict], decay: float = 0.5) -> dict[str, float]:    
    start_node = normalize_name(start_node)
    adj = _build_reverse_adjacency(edges)

    visited = {start_node: 1.0}
    queue = collections.deque([start_node])

    while queue:
        curr = queue.popleft()
        curr_score = visited[curr]

        for dep, weight in adj.get(curr, []):
            new_score = curr_score * weight * decay
            if dep not in visited or new_score > visited[dep]:
                visited[dep] = new_score
                queue.append(dep)
    return visited

def simulate_cascade(start_node: str, decay: float = 0.5) -> dict[str, float]:  
    graph = fetch_graph()
    return run_simulation(start_node, graph.get("edges"), decay)  
