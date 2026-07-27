"""
python -m tests.test_simulate
"""

from simulate import run_simulation
 
edges = [
    {"source": "A", "target": "B", "impactWeight": "1.0"},
    {"source": "B", "target": "C", "impactWeight": "1.0"},
    {"source": "D", "target": "C", "impactWeight": "1.0"},  
]
 
result = run_simulation("C", edges, decay=0.5)

assert result["c"] == 1.0, "origin node should have score 1.0"
assert result["b"] < result["c"], "b"
assert result["a"] < result["b"], "c"
print(f"PASS: {result}")
 