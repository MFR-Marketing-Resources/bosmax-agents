"""
flow_bridge — the OTAK side of the OTAK <-> TANGAN seam.

OTAK  = BOSMAX Command Centre (this repo): builds prompts + start-frame briefs.
TANGAN = _ref_flowkit FastAPI service on :8100: executes on Google Flow.

This package is the *only* thing that knows about the seam. It:
  - projects a BOSMAX compiled video template -> the contract-5 envelope (envelope.py)
  - POSTs to the TANGAN service over config-driven HTTP (client.py)

Two repos, zero git coupling. Base URL = env FLOW_API_BASE.
Authoritative seam spec: _ref_flowkit/docs/INTEGRATION_CONTRACT.md
"""

from .envelope import (
    ASPECT_LANDSCAPE,
    ASPECT_PORTRAIT,
    MODE_AI,
    MODE_UPLOAD,
    TIER_ONE,
    TIER_TWO,
    Envelope,
    EnvelopeError,
    StartFrame,
    project,
)
from .client import FlowError, FlowExecClient

__all__ = [
    "project", "Envelope", "StartFrame", "EnvelopeError",
    "FlowExecClient", "FlowError",
    "ASPECT_PORTRAIT", "ASPECT_LANDSCAPE", "MODE_AI", "MODE_UPLOAD",
    "TIER_ONE", "TIER_TWO",
]
