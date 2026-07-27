# sparqlwrapper wrapper
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from importers.base import normalize_name
from dotenv import load_dotenv
import os

load_dotenv()
FUSEKI_USER = os.environ.get("FUSEKI_USER", "admin")
FUSEKI_PASSWORD = os.environ.get("FUSEKI_ADMIN_PASSWORD", "")
FUSEKI_ENDPOINT = "http://localhost:3030/blastradius/sparql"
FUSEKI_UPDATE_ENDPOINT = "http://localhost:3030/blastradius/update"


GRAPH_QUERY = """
PREFIX br: <http://blastradius.dev/ontology#>

SELECT ?service ?dependency ?impactWeight
WHERE {
  << ?service br:dependsOn ?dependency >> br:impactWeight ?impactWeight .
}
"""

NODES_QUERY = """
PREFIX br: <http://blastradius.dev/ontology#>

SELECT ?service
WHERE {
  ?service a br:Service .
}
"""


def fetch_graph() -> dict:
    wrapper = SPARQLWrapper(FUSEKI_ENDPOINT)
    wrapper.setQuery(GRAPH_QUERY)
    wrapper.setReturnFormat(JSON)
    graph = wrapper.queryAndConvert()["results"]["bindings"]

    nodes, edges = set(), []
    for edge_dict in graph:
        source_uri = (edge_dict.get("service")).get("value")
        target_uri = (edge_dict.get("dependency")).get("value")
        impactWeight = (edge_dict.get("impactWeight", {})).get("value")

        source = str(source_uri).split("#")[-1]
        target = str(target_uri).split("#")[-1]

        nodes.add(source)
        nodes.add(target)

        edge = {"source": source, "target": target, "edge_type": "dependsOn"}
        if impactWeight:
            edge["impactWeight"] = impactWeight

        edges.append(edge)

    wrapper2 = SPARQLWrapper(FUSEKI_ENDPOINT)  # for isolated nodes
    wrapper2.setQuery(NODES_QUERY)
    wrapper2.setReturnFormat(JSON)
    service_bindings = wrapper2.queryAndConvert()["results"]["bindings"]

    for row in service_bindings:
        uri = row["service"]["value"]
        nodes.add(uri.split("#")[-1])

    return {"nodes": list(nodes), "edges": edges}


def _run_update(update_query: str) -> None:
    wrapper = SPARQLWrapper(FUSEKI_UPDATE_ENDPOINT)
    wrapper.setMethod(POST)
    wrapper.setQuery(update_query)
    wrapper.setCredentials(FUSEKI_USER, FUSEKI_PASSWORD)
    wrapper.query()


def insert_node(name: str) -> None:
    name = normalize_name(name)
    INSERT_NODE_QUERY = f"""
    PREFIX br: <http://blastradius.dev/ontology#>

    INSERT DATA {{ br:{name} a br:Service . }} 
    """  # TODO: vulnerable to injection
    _run_update(INSERT_NODE_QUERY)


def insert_edge(source: str, target: str, impact_weight: float | None = None) -> None:
    source = normalize_name(source)
    target = normalize_name(target)
    INSERT_EDGE_QUERY = f"""
      PREFIX br: <http://blastradius.dev/ontology#>

      INSERT DATA {{ br:{source} br:dependsOn br:{target} . }} 
      """  # TODO: vulnerable to injection
    _run_update(INSERT_EDGE_QUERY)
    if impact_weight:
        INSERT_WEIGHT_QUERY = f"""
      PREFIX br: <http://blastradius.dev/ontology#>

      INSERT DATA {{ << br:{source} br:dependsOn br:{target} >>
                        br:impactWeight {impact_weight} . }} 
      """  # TODO: vulnerable to injection
        _run_update(INSERT_WEIGHT_QUERY)


def delete_node(name: str) -> int:
    name = normalize_name(name)
    SELECT_AFFECTED_QUERY = f"""
      PREFIX br: <http://blastradius.dev/ontology#>

      SELECT ?service ?dependency
      WHERE {{
        {{ br:{name} br:dependsOn ?dependency . BIND(br:{name} AS ?service) }}
        UNION
        {{ ?service br:dependsOn br:{name} . BIND(br:{name} AS ?dependency) }}
      }}
    """
    wrapper = SPARQLWrapper(FUSEKI_ENDPOINT)
    wrapper.setQuery(SELECT_AFFECTED_QUERY)
    wrapper.setReturnFormat(JSON)
    graph = wrapper.queryAndConvert()["results"]["bindings"]
    print(graph)
    count = 0
    for edge in graph:
        source_uri = edge.get("service").get("value")
        target_uri = edge.get("dependency").get("value")
        source = str(source_uri).split("#")[-1]
        target = str(target_uri).split("#")[-1]
        delete_edge(source, target)
        count += 1
    DELETE_NODE_QUERY = f"""      
      PREFIX br: <http://blastradius.dev/ontology#>

      DELETE DATA {{ br:{name} a br:Service . }}
    """
    _run_update(DELETE_NODE_QUERY)
    return count


def delete_edge(source: str, target: str) -> None:
    source = normalize_name(source)
    target = normalize_name(target)
    DELETE_EDGE_QUERY = f"""
      PREFIX br: <http://blastradius.dev/ontology#>

      DELETE DATA {{ br:{source} br:dependsOn br:{target} . }} 
      """
    _run_update(DELETE_EDGE_QUERY)

    DELETE_WEIGHT_QUERY = f"""
      PREFIX br: <http://blastradius.dev/ontology#>

      DELETE WHERE {{
        << br:{source} br:dependsOn br:{target} >> br:impactWeight ?w .
      }}
    """
    _run_update(DELETE_WEIGHT_QUERY)

def get_blast_radius(name: str) -> list[str]:
    name = normalize_name(name)

    BLAST_RADIUS_QUERY = f"""
      PREFIX br: <http://blastradius.dev/ontology#>

      SELECT ?affected
      WHERE {{ ?affected br:dependsOn+ br:{name} . }} 
      """
    
    wrapper = SPARQLWrapper(FUSEKI_ENDPOINT)
    wrapper.setQuery(BLAST_RADIUS_QUERY)
    wrapper.setReturnFormat(JSON)
    graph = wrapper.queryAndConvert()["results"]["bindings"]

    ans = set()
    for node in graph:
        node_uri = node.get("affected").get("value")
        node = str(node_uri).split("#")[-1]
        ans.add(node)
    return list(ans)
