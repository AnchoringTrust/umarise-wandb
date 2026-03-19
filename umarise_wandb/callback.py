"""Auto-anchor callback for W&B."""

import threading
from typing import Optional

import wandb
from umarise_wandb.anchor import anchor_artifact as _anchor


class AnchorCallback:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._lock = threading.Lock()

    def on_artifact_log(self, artifact: wandb.Artifact, **kwargs):
        with self._lock:
            try:
                _anchor(artifact, api_key=self.api_key)
            except Exception:
                pass


_original_log_artifact = None
_enabled = False


def enable(api_key: Optional[str] = None):
    global _original_log_artifact, _enabled
    if _enabled:
        return
    from umarise import UmariseCore
    import hashlib
    import os
    client = UmariseCore(api_key=api_key)
    _original_log_artifact = wandb.Run.log_artifact

    def _patched_log_artifact(self, artifact, *args, **kwargs):
        result = _original_log_artifact(self, artifact, *args, **kwargs)
        try:
            if hasattr(artifact, 'manifest') and artifact.manifest:
                for entry in artifact.manifest.entries.values():
                    if entry.local_path and os.path.exists(entry.local_path):
                        h = hashlib.sha256()
                        with open(entry.local_path, "rb") as f:
                            for chunk in iter(lambda: f.read(8192), b""):
                                h.update(chunk)
                        file_hash = f"sha256:{h.hexdigest()}"
                        anchor_result = client.attest(hash=file_hash)
                        if wandb.run:
                            wandb.run.summary["umarise_anchored"] = True
                            wandb.run.summary["umarise_last_origin_id"] = anchor_result.get("origin_id")
        except Exception:
            pass
        return result

    wandb.Run.log_artifact = _patched_log_artifact
    _enabled = True


def disable():
    global _original_log_artifact, _enabled
    if _original_log_artifact:
        wandb.Run.log_artifact = _original_log_artifact
        _original_log_artifact = None
    _enabled = False
