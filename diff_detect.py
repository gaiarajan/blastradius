import subprocess

import yaml

from importers.compose import ComposeImporter
from importers.k8s import K8sImporter


def get_changed_files(base_ref: str | None = None, head_ref: str | None = None) -> list[str]:
    if base_ref and head_ref:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"],
            capture_output=True, text=True, check=True,
        )
        return [line for line in result.stdout.splitlines() if line.strip()]

    tracked = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=True,
    )

    files = tracked.stdout.splitlines() + untracked.stdout.splitlines()
    return [line for line in files if line.strip()]


def _detect_importer_type(path: str) -> str | None:
    if not path.endswith((".yml", ".yaml")):
        return None

    try:
        with open(path, "r") as f:
            # multi-doc load for k8s
            docs = list(yaml.safe_load_all(f))
    except (yaml.YAMLError, FileNotFoundError):
        # FileNotFoundError: file was deleted in this diff
        return None

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        if "services" in doc:
            return "compose"
        if "kind" in doc and doc["kind"] in ("Service", "Deployment"):
            return "k8s"

    return None


def get_touched_services(base_ref: str | None = None, head_ref: str | None = None) -> set[str]:
    touched = set()

    for path in get_changed_files(base_ref, head_ref):
        importer_type = _detect_importer_type(path)
        if importer_type is None:
            continue

        importer_cls = {"compose": ComposeImporter, "k8s": K8sImporter}[importer_type]
        try:
            result = importer_cls().parse(path)
        except Exception as e:
            # malformed/partial file shouldn't crash everything
            print(f"warning: could not parse {path}: {e}")
            continue

        touched |= result.nodes

    return touched
