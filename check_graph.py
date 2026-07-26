from sparql_client import fetch_graph

result = fetch_graph()

print("Nodes:", result.get("nodes"))
print()
print("Edges:", result.get("edges"))
print()
print(f"({len(result.get('nodes', []))} nodes, {len(result.get('edges', []))} edges)")
