"""
Integration test for the OTAK client against the §4 one-shot async lifecycle.

Mocks the HTTP transport (no network, no live backend) so it pins the client's
contract with /shoot-oneshot + /job/{id} exactly as TANGAN now returns them:
  POST /api/flow/shoot-oneshot (envelope §5) -> { job_id, status }   (202)
  GET  /api/flow/job/{id} -> { status, video_url, local_path, media_id, error }

When the live backend is up, this same flow runs for real with one line changed.

Run:  python -m unittest flow_bridge.tests.test_oneshot -v
"""

from __future__ import annotations

import unittest

from flow_bridge.client import FlowError, FlowExecClient
from flow_bridge.envelope import project

COMPILED = {
    "identity": {"engine": "GOOGLE_FLOW", "platform": "TikTok Shop MY"},
    "product": {"product_truth_lock": "BOSMAX Serum 5ML.", "scale_lock": "lip balm size."},
    "angle": {"scene_context_seed": "Dalam kereta, sapu pada pergelangan."},
    "storyboard": {"block_script_json": [{"flow_prompt": "Push-in, product sharp."}]},
}


class _ScriptedClient(FlowExecClient):
    """FlowExecClient with _request replaced by a scripted responder."""

    def __init__(self, job_timeline):
        super().__init__(base="http://test")
        self.calls = []
        self._timeline = list(job_timeline)
        self._sent_envelope = None

    def _request(self, method, path, body=None, *, timeout=None):
        self.calls.append((method, path, body))
        if path == "/api/flow/shoot-oneshot":
            self._sent_envelope = body
            return {"job_id": "j_test", "status": "SUBMITTED"}
        if path.startswith("/api/flow/job/"):
            # pop the next scripted job state (last one repeats)
            return self._timeline.pop(0) if len(self._timeline) > 1 else self._timeline[0]
        raise AssertionError(f"unexpected call: {method} {path}")


class TestOneShotLifecycle(unittest.TestCase):
    def test_submit_sends_exact_envelope(self):
        c = _ScriptedClient([{"status": "SUCCESSFUL", "video_url": "u", "local_path": "p", "media_id": "m"}])
        env = project(COMPILED)
        resp = c.shoot_oneshot(env.to_dict())
        self.assertEqual(resp["job_id"], "j_test")
        # the body POSTed must be exactly the contract-5 envelope
        self.assertEqual(set(c._sent_envelope), {"prompt", "aspect_ratio", "user_paygate_tier", "start_frame"})

    def test_poll_until_successful(self):
        timeline = [
            {"status": "RUNNING_FRAME", "stage": "frame"},
            {"status": "SUBMITTED_VIDEO", "stage": "video"},
            {"status": "SUCCESSFUL", "video_url": "https://v/x", "local_path": "/tmp/x.mp4", "media_id": "uuid"},
        ]
        c = _ScriptedClient(timeline)
        final = c.poll_job("j_test", interval=0, timeout=5)
        self.assertEqual(final["status"], "SUCCESSFUL")
        self.assertEqual(final["video_url"], "https://v/x")
        self.assertEqual(final["local_path"], "/tmp/x.mp4")     # the durable artifact (URLs expire)

    def test_poll_returns_failed_without_raising(self):
        c = _ScriptedClient([{"status": "FAILED", "error": "tier NOT_PAID — perlu Pro/Ultra"}])
        final = c.poll_job("j_test", interval=0, timeout=5)
        self.assertEqual(final["status"], "FAILED")
        self.assertIn("Pro", final["error"])

    def test_timeout_raises(self):
        c = _ScriptedClient([{"status": "RUNNING_FRAME"}])  # never completes
        with self.assertRaises(FlowError):
            c.poll_job("j_test", interval=0, timeout=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
