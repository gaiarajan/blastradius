"""
uvicorn main:app --reload
 http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from sparql_client import fetch_graph

app = FastAPI()


@app.get("/graph")
def get_graph():
    return fetch_graph()
