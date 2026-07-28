import argparse

from importers.compose import ComposeImporter
from importers.k8s import K8sImporter
from importers.base import normalize_name

from sparql_client import insert_node, insert_edge, get_blast_radius, get_fallback_edges, fetch_graph

IMPORTERS = {
    "compose": ComposeImporter,
    "k8s": K8sImporter,
}

def cmd_import(args):
    importer_cls = IMPORTERS[args.source]
    importer = importer_cls()

    result = importer.parse(args.path)

    for node in result.nodes:
        insert_node(node)

    for edge in result.edges:
        insert_edge(edge.source, edge.target, edge.weight)

    print(f"imported {len(result.nodes)} nodes, {len(result.edges)} edges from {args.path}")


def cmd_check(args):
    node = normalize_name(args.node)
    affected = get_blast_radius(node)

    graph = fetch_graph()
    has_fallback = {normalize_name(s) for s, _b in get_fallback_edges()}
    direct_dependents = [e["source"] for e in graph["edges"]
                          if e["target"] == node and e["edge_type"] == "dependsOn"]
    without_fallback = [d for d in direct_dependents if d not in has_fallback]

    print(f"{len(affected)} services affected: {', '.join(sorted(affected)) or 'none'}")
    if without_fallback:
        print(f"{len(without_fallback)} without fallback: {', '.join(sorted(without_fallback))}")
    else:
        print("all direct dependents have a fallback")


def main():
    parser = argparse.ArgumentParser(prog="blastradius")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_import = subparsers.add_parser("import")
    p_import.add_argument("--source", choices=IMPORTERS.keys(), required=True)
    p_import.add_argument("path")
    p_import.set_defaults(func=cmd_import)

    p_check = subparsers.add_parser("check")
    p_check.add_argument("node")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
