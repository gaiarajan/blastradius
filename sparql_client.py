# sparqlwrapper wrapper
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE

FUSEKI_ENDPOINT = "http://localhost:3030/blastradius/sparql"

GRAPH_QUERY = """
PREFIX br:   <http://blastradius.dev/ontology#> 
CONSTRUCT {
  << ?service br:dependsOn ?dependency >> br:impactWeight ?impactWeight .
}
WHERE {
  << ?service br:dependsOn ?dependency >> br:impactWeight ?impactWeight .
}
"""


def fetch_graph() -> dict:
    wrapper = SPARQLWrapper(FUSEKI_ENDPOINT)
    wrapper.setQuery(GRAPH_QUERY)
    wrapper.setReturnFormat(TURTLE)
    graph = wrapper.queryAndConvert()
    print(graph) #TODO: parsing loop
    return {}


