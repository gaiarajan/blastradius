from sparql_client import fetch_graph, insert_node, insert_edge, delete_node

result = fetch_graph()

print("Nodes:", result.get("nodes"))
print()
print("Edges:", result.get("edges"))
print()
print(f"({len(result.get('nodes', []))} nodes, {len(result.get('edges', []))} edges)")

insert_node("authService2")
insert_edge("authService", "authService2", 0.9)

result = fetch_graph()

print("Nodes:", result.get("nodes"))
print()
print("Edges:", result.get("edges"))
print()
print(f"({len(result.get('nodes', []))} nodes, {len(result.get('edges', []))} edges)")

delete_node("authService")
delete_node("authService2")

result = fetch_graph()

print("Nodes:", result.get("nodes"))
print()
print("Edges:", result.get("edges"))
print()
print(f"({len(result.get('nodes', []))} nodes, {len(result.get('edges', []))} edges)")
