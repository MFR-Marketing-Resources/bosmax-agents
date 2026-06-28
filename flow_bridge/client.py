"""
Thin HTTP client for the TANGAN service (_ref_flowkit FastAPI on :8100).

Cloud-ready rule (contract section 1): the base URL is config-driven via the
FLOW_API_BASE env var, never hardcoded. Swap one env var to point at a hosted box.

Pure stdlib (urllib). Maps 1:1 to the endpoints verified in agent/api/flow.py.
The one-shot async endpoints (/shoot-oneshot, /job/{id}) are wired here too but
guarded — they only exist once the TANGAN side builds them (contract section 4).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

DEFAULT_BASE = "http://127.0.0.1:8100"


class FlowError(RuntimeError):
    """Non-2xx from the TANGAN service. status maps to the contract section 6:
    503 = extension not connected, 502 = upstream Google error, 500 = tier/no-model."""

    def __init__(self, status: int, message: str, body: Any = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message
        self.body = body


@dataclass
class FlowExecClient:
    base: str = ""
    timeout: float = 30.0

    def __post_init__(self) -> None:
        self.base = (self.base or os.environ.get("FLOW_API_BASE") or DEFAULT_BASE).rstrip("/")

    # ---- transport --------------------------------------------------------
    def _request(self, method: str, path: str, body: Optional[dict] = None, *, timeout: Optional[float] = None) -> Any:
        url = f"{self.base}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                raw = resp.read().decode() or "null"
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode() if e.fp else ""
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = raw
            msg = ""
            if isinstance(parsed, dict):
                msg = str(parsed.get("detail") or parsed.get("error") or parsed)
            else:
                msg = str(parsed)
            raise FlowError(e.code, msg or e.reason, parsed) from None
        except urllib.error.URLError as e:
            raise FlowError(0, f"connection failed ({e.reason}) — is the TANGAN backend up at {self.base}?") from None

    # ---- read-only / preconditions (contract section 2) -------------------
    def health(self) -> dict:
        """{ extension_connected, flow_key_present, tier? }"""
        return self._request("GET", "/health", timeout=8)

    def status(self) -> dict:
        return self._request("GET", "/api/flow/status", timeout=8)

    def credits(self) -> dict:
        """{ credits, userPaygateTier, sku, ... } — free, read-only."""
        return self._request("GET", "/api/flow/credits", timeout=15)

    def ready(self) -> tuple[bool, list[str]]:
        """Check the 3 preconditions. Returns (ok, reasons_not_ready)."""
        reasons: list[str] = []
        try:
            h = self.health()
        except FlowError as e:
            return False, [e.message]
        if not h.get("extension_connected"):
            reasons.append("extension not connected (open + log in to a Flow tab)")
        if not h.get("flow_key_present"):
            reasons.append("flow token not captured yet")
        return (not reasons), reasons

    def is_paid(self) -> tuple[bool, str]:
        tier = str(self.credits().get("userPaygateTier", "PAYGATE_TIER_NOT_PAID"))
        return (tier in ("PAYGATE_TIER_ONE", "PAYGATE_TIER_TWO")), tier

    # ---- build blocks (contract section 3) --------------------------------
    def create_project(self, title: str, tool_name: str = "PINHOLE") -> str:
        r = self._request("POST", "/api/flow/create-project-raw",
                           {"project_title": title, "tool_name": tool_name})
        pid = _dig(r, "projectId") or _dig(r, "project", "projectId") or _dig(r, "data", "projectId")
        if not pid:
            raise FlowError(502, f"create-project returned no projectId: {r}")
        return str(pid)

    def generate_image(self, prompt: str, project_id: str, *,
                       aspect_ratio: str = "IMAGE_ASPECT_RATIO_PORTRAIT",
                       user_paygate_tier: str = "PAYGATE_TIER_ONE") -> dict:
        """AI frame. Works on freemium, 0 credits. Returns dict with media_id + fifeUrl."""
        r = self._request("POST", "/api/flow/generate-image", {
            "prompt": prompt, "project_id": project_id,
            "aspect_ratio": aspect_ratio, "user_paygate_tier": user_paygate_tier})
        return _media_summary(r)

    def upload_image_base64(self, image_base64: str, project_id: str, *,
                            mime_type: str = "image/png", file_name: str = "product.png") -> dict:
        r = self._request("POST", "/api/flow/upload-image-base64", {
            "image_base64": image_base64, "mime_type": mime_type,
            "project_id": project_id, "file_name": file_name})
        return _media_summary(r)

    def generate_video(self, *, start_image_media_id: str, prompt: str, project_id: str,
                       scene_id: str, aspect_ratio: str = "VIDEO_ASPECT_RATIO_PORTRAIT",
                       end_image_media_id: Optional[str] = None,
                       user_paygate_tier: str = "PAYGATE_TIER_ONE") -> dict:
        """Submit i2v. Returns operations[] for polling (NOT the video)."""
        return self._request("POST", "/api/flow/generate-video", {
            "start_image_media_id": start_image_media_id, "prompt": prompt,
            "project_id": project_id, "scene_id": scene_id, "aspect_ratio": aspect_ratio,
            "end_image_media_id": end_image_media_id, "user_paygate_tier": user_paygate_tier})

    def check_status(self, operations: list) -> dict:
        return self._request("POST", "/api/flow/check-status", {"operations": operations})

    # ---- one-shot async (contract section 4 — exists once TANGAN builds it) -
    def shoot_oneshot(self, envelope: dict) -> dict:
        """POST the OTAK envelope. -> { job_id, status } (202)."""
        return self._request("POST", "/api/flow/shoot-oneshot", envelope)

    def job(self, job_id: str) -> dict:
        return self._request("GET", f"/api/flow/job/{job_id}", timeout=15)

    def poll_job(self, job_id: str, *, interval: float = 10.0, timeout: float = 420.0) -> dict:
        """Poll /job/{id} until SUCCESSFUL/FAILED or timeout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            j = self.job(job_id)
            st = str(j.get("status", "")).upper()
            if st in ("SUCCESSFUL", "FAILED"):
                return j
            time.sleep(interval)
        raise FlowError(0, f"job {job_id} timed out after {timeout}s")


# ---- small extractors ------------------------------------------------------

def _dig(obj: Any, *keys: str) -> Any:
    cur = obj
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur


def _media_summary(resp: Any) -> dict:
    """Normalise the TWO distinct TANGAN media response shapes to a common dict:

      upload-image / upload-image-base64 -> {"media_id": "...", "local_file_path": "...", "raw": {...}}
          (top-level media_id, from handler's _mediaId — verified agent/api/flow.py:440,470)
      generate-image -> data payload with media[0].name + image.generatedImage.fifeUrl

    Returns {media_id, fife_url, local_path, raw}. Raises if no media_id (fail loud).
    """
    media_id = None
    fife = None
    local_path = None
    if isinstance(resp, dict):
        if resp.get("media_id"):
            # upload responses: clean top-level media_id
            media_id = resp["media_id"]
            local_path = resp.get("local_file_path")
        else:
            # generate-image: dig into media[0]
            m = resp.get("media")
            if isinstance(m, list) and m:
                media = m[0]
            elif isinstance(m, dict):
                media = m
            elif "name" in resp:
                media = resp
            else:
                media = {}
            media_id = media.get("name") or _dig(media, "image", "generatedImage", "mediaId")
            fife = _dig(media, "image", "generatedImage", "fifeUrl") or media.get("fifeUrl")
    if not media_id:
        raise FlowError(502, f"no media_id in response: {resp}")
    return {"media_id": str(media_id), "fife_url": fife, "local_path": local_path, "raw": resp}
