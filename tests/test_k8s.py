"""
Expected nodes: auth_service, user_db, metrics_service
Expected edges:
  auth_service --[dependsOn]--> user_db   (confidence=low, origin=k8s)
  (inferred from DB_URL env var referencing "user-db")
"""
import os

from importers.k8s import K8sImporter

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'k8s_sample.yaml')

result = K8sImporter().parse(FIXTURE_PATH)

print('Nodes:', sorted(result.nodes))
print()
print('Edges:')
for e in result.edges:
    print(f'  {e.source} --[{e.edge_type}]--> {e.target}  '
          f'(origin={e.origin}, confidence={e.confidence})')
