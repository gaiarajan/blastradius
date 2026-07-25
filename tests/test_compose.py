"""
Expected nodes: api, cache, db, frontend, standalone_worker
Expected edges:
  frontend --[dependsOn]--> api 
  api --[dependsOn]--> db
  api --[links]--> cache
"""
import os

from importers.compose import ComposeImporter

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'compose_sample.yml')

result = ComposeImporter().parse(FIXTURE_PATH)

print('Nodes:', sorted(result.nodes))
print()
print('Edges:')
for e in result.edges:
    print(f'  {e.source} --[{e.edge_type}]--> {e.target}  (origin={e.origin})')
    