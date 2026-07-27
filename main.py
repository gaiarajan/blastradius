"""
uvicorn main:app --reload
 http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from pydantic import BaseModel
from sparql_client import fetch_graph, insert_node, insert_edge, delete_node, delete_edge, get_blast_radius
from simulate import simulate_cascade

app = FastAPI()

class NodeCreate(BaseModel):
    name: str
 
class EdgeCreate(BaseModel):
    source: str
    target: str
    impact_weight: float | None = None

@app.get("/graph")
def get_graph():
    return fetch_graph()
 
@app.get("/blast-radius/{name}")
def blast_radius_route(name: str):
    affected = get_blast_radius(name)
    return {"node": name, "affected": affected}

@app.get("/simulate/{name}")
def simulate_route(name: str, decay: float = 0.5):
    impact = simulate_cascade(name, decay)
    return {"node": name, "impact": impact}

@app.post("/nodes", status_code=201)
def create_node(node: NodeCreate):
    insert_node(node.name)
    return {"created": node.name}
 
@app.post("/edges", status_code=201)
def create_edge(edge: EdgeCreate):
    insert_edge(edge.source, edge.target, edge.impact_weight),
    return {"created": f"{edge.source} -> {edge.target}"}
 
@app.delete("/nodes/{name}")
def delete_node_route(name: str):
    n = delete_node(name)
    return {"deleted_node": name, "edges_removed": N}
 
@app.delete("/edges")
def delete_edge_route(source: str, target: str):
    delete_edge(source, target)
    return {"deleted_source": source, "deleted_target": target}
