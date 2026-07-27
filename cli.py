import argparse

from importers.compose import ComposeImporter
from importers.k8s import K8sImporter

from sparql_client import insert_node, insert_edge

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

    print(result)

def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("import")
    p.add_argument("--source", choices=IMPORTERS.keys(), required=True)
    p.add_argument("path")
    p.set_defaults(func=cmd_import)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
