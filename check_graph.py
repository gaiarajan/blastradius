from sparql_client import fetch_graph, insert_node, insert_edge, delete_node, delete_edge, get_blast_radius

def print_graph():
   result = fetch_graph()

   print("Nodes:", result.get("nodes"))
   print()
   print("Edges:", result.get("edges"))
   print()
   print(f"({len(result.get('nodes', []))} nodes, {len(result.get('edges', []))} edges)")

print_graph() 

insert_node("authService2")
insert_edge("authService", "authService2", 0.9)

print_graph()

delete_node("authService")

print_graph()

insert_node("authService3")
insert_edge("authService2", "authService3", 0.9)
insert_edge("authService3", "authService2", 0.9)

print(get_blast_radius("authService2"))
