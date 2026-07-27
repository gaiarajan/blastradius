"""
Shared interface for all importers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import re


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