"""
umarise-wandb: Anchor W&B artifacts to Bitcoin.

Usage:
    import umarise_wandb
    umarise_wandb.enable()
"""

from umarise_wandb.anchor import anchor_artifact, anchor_logged_artifact
from umarise_wandb.callback import AnchorCallback, enable

__version__ = "0.1.0"
__all__ = ["anchor_artifact", "anchor_logged_artifact", "AnchorCallback", "enable"]
