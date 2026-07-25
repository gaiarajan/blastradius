"""
Docker Compose importer.

Handles the two shapes of `depends_on`:
    depends_on:
      - db
      - redis
and:
    depends_on:
      db:
        condition: service_healthy

Also handles `links`, which is an older field that sometimes has
"servicename:alias" syntax.

"""

import yaml

from .base import Edge, ImportResult, Importer, normalize_name


class ComposeImporter(Importer):

    # "skip" | "warn" | "stub"
    ON_MISSING_REFERENCE = "skip"

    def parse(self, path: str) -> ImportResult:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        services = data.get('services', {})
        res = ImportResult()

        for service in services:
            res.add_node(normalize_name(service))
        
        for service, config in services.items():
            source = normalize_name(service)
            depends_list = self._extract_depends_on(config)
            links_list = self._extract_links(config)
            for depends_node in depends_list:
                self._emit_edge(res, source, depends_node, services, "dependsOn")
            for links_node in links_list:
                self._emit_edge(res, source, links_node, services, "links")
        return res

    def _extract_depends_on(self, config: dict) -> list[str]:
        res = config.get("depends_on", [])
        if isinstance(res, dict):
            return list(res.keys())
        return res

    def _extract_links(self, config: dict) -> list[str]:
        res = (config.get("links", []))
        ans = [(r.split(":"))[0] for r in res]
        return ans

    def _emit_edge(self, result: ImportResult, source: str, target_raw: str,
                   services: dict, edge_type: str) -> None:
        target = normalize_name(target_raw)
        if target_raw not in services:
            if self.ON_MISSING_REFERENCE == "skip":
                return
            elif self.ON_MISSING_REFERENCE == "warn":
                print("WARNING")
            else:
                result.add_node(target)
        e = Edge(source, target, edge_type, weight = None, origin = "compose")
        result.add_edge(e)