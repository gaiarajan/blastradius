# sparqlwrapper wrapper
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE
from rdflib import Graph
FUSEKI_ENDPOINT = "http://localhost:3030/blastradius/sparql"

GRAPH_QUERY = """
PREFIX br: <http://blastradius.dev/ontology#>

SELECT ?service ?dependency ?impactWeight
WHERE {
  << ?service br:dependsOn ?dependency >> br:impactWeight ?impactWeight .
}
"""


def fetch_graph() -> dict:
    wrapper = SPARQLWrapper(FUSEKI_ENDPOINT)
    wrapper.setQuery(GRAPH_QUERY)
    wrapper.setReturnFormat(JSON)
    graph = wrapper.queryAndConvert()['results']['bindings']

    nodes, edges = set(), []
    for edge_dict in graph:
        source_uri = (edge_dict.get('service')).get('value')
        target_uri = (edge_dict.get('dependency')).get('value')
        impactWeight = (edge_dict.get('impactWeight', {})).get('value')

        source = str(source_uri).split('#')[-1]
        target = str(target_uri).split('#')[-1]

        nodes.add(source)
        nodes.add(target)

        edge = {"source": source, "target": target, "edge_type": "dependsOn"}
        if impactWeight:
            edge["impactWeight"] = impactWeight

        edges.append(edge)

    return {"nodes": list(nodes), "edges": edges}
