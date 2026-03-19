"""Core anchoring functions for W&B artifacts."""

import hashlib
import os
from typing import Optional

import wandb
from umarise import UmariseCore


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def anchor_artifact(artifact: wandb.Artifact, api_key: Optional[str] = None) -> list:
    client = UmariseCore(api_key=api_key)
    results = []
    for entry in artifact.manifest.entries.values():
        if entry.local_path and os.path.exists(entry.local_path):
            file_hash = _hash_file(entry.local_path)
            result = client.attest(hash=file_hash)
            result["artifact_name"] = artifact.name
            result["entry_path"] = entry.path
            results.append(result)
            if wandb.run:
                wandb.log({"umarise/origin_id": result.get("origin_id"), "umarise/anchored": True})
    return results


def anchor_logged_artifact(artifact_name: str, version: str = "latest", api_key: Optional[str] = None) -> list:
    if not wandb.run:
        raise RuntimeError("No active W&B run. Call wandb.init() first.")
    ref = f"{artifact_name}:{version}" if ":" not in artifact_name else artifact_name
    artifact = wandb.run.use_artifact(ref)
    artifact_dir = artifact.download()
    client = UmariseCore(api_key=api_key)
    results = []
    for root, _, files in os.walk(artifact_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            file_hash = _hash_file(fpath)
            result = client.attest(hash=file_hash)
            result["file"] = os.path.relpath(fpath, artifact_dir)
            results.append(result)
    if results:
        wandb.log({"umarise/artifact_count": len(results), "umarise/anchored": True})
    return results
