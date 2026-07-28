"""
Shared interface for all importers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import re
import yaml

def detect_importer_type(path: str) -> str | None:
    if not path.endswith((".yml", ".yaml")):
        return None
    try:
        with open(path, "r") as f:
            docs = list(yaml.safe_load_all(f))
    except (yaml.YAMLError, FileNotFoundError):
        return None

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        if "services" in doc:
            return "compose"
        if "kind" in doc and doc["kind"] in ("Service", "Deployment"):
            return "k8s"
    return None


def normalize_name(name: str) -> str:
    """
    Service-Name -> service_name
    ServiceName -> service_name
    """
    name = name.strip()
    name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    name = name.lower().replace('-', '_').replace(' ', '_')
    return name


@dataclass
class Edge:
    """
    Dependency/relationship edge between two services.
    """
    source: str
    target: str
    edge_type: str = "dependsOn"
    weight: Optional[float] = None
    origin: str = "unknown"
    confidence: str = "high"


@dataclass
class ImportResult:
    edges: list[Edge] = field(default_factory=list)
    nodes: set[str] = field(default_factory=set)

    def add_edge(self, edge) -> None:
        self.edges.append(edge)
        self.nodes.add(edge.source)
        self.nodes.add(edge.target)

    def add_node(self, name) -> None:
        self.nodes.add(name)



class Importer(ABC):

    @abstractmethod
    def parse(self, path: str) -> ImportResult:
        ...