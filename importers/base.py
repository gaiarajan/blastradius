"""
Shared interface for all importers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


def normalize_name(name: str) -> str:
    """
    Service-Name -> service_name
    """
    return (str.lower(name.strip())).replace('-', '_')


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