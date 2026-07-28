"""
Kubernetes importer.

K8s has no explicit "depends_on" field.

1. Match service selectors to deployment pod labels.
2. Scan each deployment's env var values for another known service's
   name. This is an inferred dependsOn edge (confidence="low"),
   using the service name from step 1 as source.

"""

import yaml

from .base import Edge, ImportResult, Importer, normalize_name


class K8sImporter(Importer):

    def parse(self, path: str) -> ImportResult:
        with open(path, "r") as f:
            data_iter = list(yaml.safe_load_all(f))
        services, deployments = [], []
        res = ImportResult()

        for item in data_iter:
            kind = item.get('kind', '')
            if kind == 'Deployment':
                deployments.append(item)
            elif kind == 'Service':
                services.append(item)

        for service in services:
            res.add_node(normalize_name(self._get_name(service)))

        dep_ser_map = {} # deployment name: service name
        for service in services:
            selector = self._get_selector(service)
            for deployment in deployments:
                labels = self._get_pod_labels(deployment)
                if self._selector_matches(selector, labels):
                    dep, ser = normalize_name(self._get_name(deployment)), normalize_name(self._get_name(service))
                    dep_ser_map[dep] = ser
                    break
        
        for deployment in deployments:
            env_vars = self._extract_env_vars(deployment)
            dep_key = normalize_name(self._get_name(deployment))
            if dep_key not in dep_ser_map:
                continue
            source = dep_ser_map[dep_key]
            
            for _, env_value in env_vars:
                for service in services:
                    service_name = self._get_name(service)
                    if service_name in env_value:
                        target = normalize_name(service_name)
                        e = Edge(source, target, "dependsOn", weight=1.0, origin = "k8s", confidence = "low")
                        res.add_edge(e)
        return res

    def _get_name(self, doc: dict) -> dict:
            return (doc.get('metadata', {})).get('name', "")
    
    def _get_selector(self, service_doc: dict) -> dict:
        return (service_doc.get('spec', {})).get('selector', {})

    def _get_pod_labels(self, deployment_doc: dict) -> dict:
        return (((deployment_doc.get('spec', {})).get('template', {})).get('metadata', {})).get('labels', {})

    def _selector_matches(self, selector: dict, pod_labels: dict) -> bool:
        return all(pod_labels.get(k) == v for k, v in selector.items())

    def _extract_env_vars(self, deployment_doc: dict) -> list[tuple[str, str]]:
        containers = (((deployment_doc.get('spec', {})).get('template', {})).get('spec', {})).get('containers', {})
        res = []
        for container in containers:
            env = container.get('env', [])
            for e in env:
                name, value = e.get('name', None), e.get('value', None)
                if name and value:
                    res.append((name, value))
        return res