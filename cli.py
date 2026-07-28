"""
Commands (replace uppercase):
python cli.py check-diff   
python cli.py check-diff(BASE, HEAD)
python cli.py check SERVICE_NAME
python cli.py import --source COMPOSE/K8s PATH_TO_FILE
"""

import argparse

import os

from diff_detect import get_touched_services

from importers.compose import ComposeImporter
from importers.k8s import K8sImporter
from importers.base import normalize_name, detect_importer_type


from sparql_client import insert_node, insert_edge, get_blast_radius, get_fallback_edges, fetch_graph

IMPORTERS = {
    "compose": ComposeImporter,
    "k8s": K8sImporter,
}

def import_file(path, importer_type):
    result = IMPORTERS[importer_type]().parse(path)

    for node in result.nodes:
        insert_node(node)

    for edge in result.edges:
        insert_edge(edge.source, edge.target, edge.weight)

    return len(result.nodes), len(result.edges)

def cmd_import(args):
    nodes, edges = import_file(args.path, args.source)
    print(f"imported {nodes} nodes, {edges} edges from {args.path}")


def cmd_import_all(args):
    total_nodes = total_edges = 0

    for dirpath, dirs, filenames in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for fname in filenames:
            path = os.path.join(dirpath, fname)
            importer_type = detect_importer_type(path)
            if importer_type is None:
                continue

            try:
                nodes, edges = import_file(path, importer_type)
                total_nodes += nodes
                total_edges += edges
            except Exception as e:
                print(f"warning: could not parse {path}: {e}")

    print(f"imported: {total_nodes} nodes, {total_edges} edges total")


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

def cmd_check_diff(args):
    touched = get_touched_services(args.base, args.head)
 
    if not touched:
        print("No service changes detected in diff")
        return
 
    for node in sorted(touched):
        print(f"\n--- {node} ---")
        cmd_check(argparse.Namespace(node=node))

def main():
    parser = argparse.ArgumentParser(prog="sparqlmotion")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_import = subparsers.add_parser("import")
    p_import.add_argument("--source", choices=IMPORTERS.keys(), required=True)
    p_import.add_argument("path")
    p_import.set_defaults(func=cmd_import)

    p_import_all = subparsers.add_parser("import-all")
    p_import_all.add_argument("root", nargs="?", default=".")
    p_import_all.set_defaults(func=cmd_import_all)

    p_check = subparsers.add_parser("check")
    p_check.add_argument("node")
    p_check.set_defaults(func=cmd_check)

    p_diff = subparsers.add_parser("check-diff")
    p_diff.add_argument("base", nargs="?", default=None)
    p_diff.add_argument("head", nargs="?", default=None)
    p_diff.set_defaults(func=cmd_check_diff)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
