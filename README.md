# Quickstart

Three options: Github Action (automatically runs on each PR), web UI, or CLI. 

## Github Action
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

## Web UI and CLI

### 0. Shared setup 

```bash
git clone https://github.com/gaiarajan/sparqlmotion.git
cd sparqlmotion

./setup.sh
```

`setup.sh` creates a `.env` file, starts Fuseki (the engine for triples), 
creates an empty dataset, and installs Python dependencies. 

If you are experiencing permission issues, run `chmod +x setup.sh` first.

`./setup.sh --reset` stops Fuseki and wipes `./fuseki/data`.

If you prefer to run the steps manually, here are the commands:

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

## CLI (ad hoc, terminal)

_You must have done the shared setup above first._

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

**Want to poke around before importing actual definitions?** 
Add seed data instead:

```bash
curl -X POST http://localhost:3030/blastradius/data \
  -H "Content-Type: text/turtle" --data-binary @ontology/schema.ttl
curl -X POST http://localhost:3030/blastradius/data \
  -H "Content-Type: text/turtle" --data-binary @ontology/seed_data.ttl

python cli.py check checkout_service
```

## Mode 2: Web UI (visual, localhost:8000)

_You must have done the shared setup above first._

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
## Why is it called that?

SPARQL is my favorite query language. 
Donnie Darko is one of my favorite movies. 

![Sparkle Sparklemotion GIF](https://c.tenor.com/PO3AUbv6aFUAAAAd/tenor.gif)
