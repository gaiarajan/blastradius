
# SPARQLMotion 

Ask _what breaks if payment-api goes down?_ and get a live answer computed from your project's Compose/K8s files, in a terminal command, a live visualization, or an automated PR comment.

Dependencies between services are represented internally as RDF triples. Existing blast-radius tools use bespoke graph structures; this project explores whether a standard RDF knowledge graph can serve a similar use case, while staying queryable and extensible via SPARQL. Read more in [Why SPARQL?](#why-sparql)


## Table of contents
1. [Demos](#demos)
2. [Quickstart](#quickstart)
3. [Why SPARQL?](#why-sparql)
4. [Technical details](#technical-details)
5. [Why did you call it that?](#why-is-this-project-called-that)
   
## Demos

In the interactive web UI:
<img width="850" alt="SPARQLMotion web UI" src="https://github.com/user-attachments/assets/b5f0331a-b8b6-4630-9815-ae798977172c" />

<br /><br />
As an automated PR comment ([example](https://github.com/gaiarajan/blastradius-action-test/pull/1)):

<img width="850" alt="SPARQLMotion Github Action" src="https://github.com/user-attachments/assets/085df82b-2b81-4e5f-854f-70890a37dd54" />

<br /><br />
In the CLI:

<img width="850" alt="SPARQLMotion CLI" src="https://github.com/user-attachments/assets/ded96e89-8fee-4674-81a9-de8f4c19e5f0" />


## Quickstart
Three options: Github Action (automatically runs on each PR), web UI, or CLI. 

### Github Action
In the repo you want to add blast-radius to:

**1. Add the following as `.github/workflows/blast-radius.yml`:**

```yaml
name: Blast Radius Check
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  blast-radius:
    runs-on: ubuntu-latest
    steps:
      - uses: gaiarajan/sparqlmotion@v1
        with:
          base-sha: ${{ github.event.pull_request.base.sha }}
          head-sha: ${{ github.event.pull_request.head.sha }}
```

Commit and push. 

**2.** Open a PR that touches a service file, and the check runs automatically.

### Web UI and CLI

#### 0. Shared setup 

```bash
git clone https://github.com/gaiarajan/sparqlmotion.git
cd sparqlmotion

./setup.sh
```

`setup.sh` creates a `.env` file, starts Fuseki (the engine for triples), 
creates an empty dataset, and installs Python dependencies. 

If you get permission issues, run `chmod +x setup.sh` first.

`./setup.sh --reset` stops Fuseki and wipes `./fuseki/data`.

If you prefer to run the steps manually, [here are the commands](#appendix).

### CLI (ad hoc, terminal)

_You must have done the [shared setup](#0-shared-setup) above first._

```bash
# import your service definitions (compose or k8s)
python cli.py import --source compose path/to/docker-compose.yml

# or import everything under a directory at once
python cli.py import-all .

# ask a quick question
python cli.py check payment-api

# see what a diff between two github commit hashes touches
python cli.py check-diff <base-sha> <head-sha>

# or check your uncommitted diff
python cli.py check-diff
```

**Want to explore without importing actual definitions?** 
Add seed data instead:

```bash
# set auth credentials
set -a; source .env; set +a
curl -v -X POST "http://localhost:3030/blastradius/data?default" \
  -u "admin:$FUSEKI_ADMIN_PASSWORD" \
  -H "Content-Type: text/turtle" --data-binary @seed/schema.ttl
curl -v -X POST "http://localhost:3030/blastradius/data?default" \
  -u "admin:$FUSEKI_ADMIN_PASSWORD" \
  -H "Content-Type: text/turtle" --data-binary @seed/seed_data.ttl

python cli.py check checkout_service
```

### Mode 2: Web UI 

_You must have done the [shared setup](#0-shared-setup) above first._

```bash
# backend (from repo root, Fuseki already running from step 0)
uvicorn main:app --reload
# API + docs at http://127.0.0.1:8000/docs
```

```bash
# frontend (separate terminal)
cd frontend
npm install
npm run dev
# open the printed localhost URL (default: http://localhost:5173)
```

The second URL above is a live graph of your project's dependencies!

## Why SPARQL?
[SPARQL](https://www.w3.org/TR/sparql11-query/) is the standard query language for RDF, which represents graph data as *triples*
(`subject–predicate–object`). 

RDF allows us to represent the dependencies between services as _relationships_ in a graph, instead of rows in lists or tables. SPARQL also fits very well with cascading service failures in a couple interesting ways: 

- It allows us to calculate recursive failures in a single property-path expression: `?affected br:dependsOn+ br:payment-api`.
- RDF-star puts metadata directly on edges, allowing us to represent criticality seamlessly within the edges themselves, rather than in a join table or a single node's properties.


## Technical details

As more code is entered into large codebases with no or little context, understanding the blast radius of a change (_without_ having to maintain a separate table through each dependency change) feels increasingly important. 

This project uses [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/) for the triple store; 
Python + [FastAPI](https://fastapi.tiangolo.com/) for the backend, using SPARQLWrapper and SPARQL queries to talk to Fuseki;
[react-force-graph](https://github.com/vasturiano/react-force-graph) for animated frontend.

Architecture diagram:

       Docker Compose      Kubernetes manifests
                 │                 │
                 └────────┬────────┘
                          ▼
              Dependency importers (importers/)
                          │
                          ▼
                 RDF knowledge graph
                 Apache Jena Fuseki
                          │
                          ▼
                 Blast radius engine
                    (SPARQL + BFS)
                 ┌────────┼─────────┐
                 ▼        ▼         ▼
                CLI    GitHub CI   Web UI

Five major layers:
1. Import layer: `importers/`. Discovers supported infrastructure files, parses Docker compose and Kubernetes manifests, normalizes resource names, produces nodes and edges.
2. Storage layer: `sparql_client.py`. All communication with Fuseki, including SPARQL queries, updates, graph fetches, etc.
3. Analysis layer: `simulate.py` (cascade simulation with BFS), `diff_detect.py` (maps Git diffs to affected services)
4. Interface layer: `cli.py` (CLI interface), `main.py`(FastAPI server), `frontend/`
5. Automation/GH action: `action.yml, .github/workflows/*`. The GitHub Action imports the repository graph, runs blast-radius analysis, and posts a summary of affected services. 

## Why is this project called that?

SPARQL is my favorite query language. 
Donnie Darko is one of my favorite movies. 

![Sparkle Sparklemotion GIF](https://c.tenor.com/PO3AUbv6aFUAAAAd/tenor.gif)

## Appendix

To run without setup script:

```bash
cat > .env <<EOF
FUSEKI_ADMIN_PASSWORD=devpassword123
FUSEKI_USER=admin
EOF

mkdir -p ./fuseki/data
chmod -R 777 ./fuseki/data

docker compose up -d fuseki

# Delay, first run can take a while.
for i in {1..60}; do curl -sf http://localhost:3030/\$/ping && break; sleep 1; done

# Create empty dataset
curl -sf -X POST http://localhost:3030/\$/datasets \
  -u admin:$FUSEKI_ADMIN_PASSWORD \
  --data 'dbName=blastradius&dbType=tdb2'

# Confirm it actually took, not implied by a 200 above
curl -s http://localhost:3030/\$/datasets

pip install -r requirements.txt --break-system-packages
```

Reset with:

```bash
docker compose down
sudo rm -rf ./fuseki/data
```

