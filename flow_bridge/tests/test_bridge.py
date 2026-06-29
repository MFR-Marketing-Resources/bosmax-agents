"""
Unit tests for the OTAK->TANGAN bridge. Pure stdlib (unittest), no network.

Pins the two things most likely to silently break the seam:
  1. The envelope §5 shape (so a BOSMAX compiler change can't drift it unnoticed).
  2. The TWO distinct media response shapes (generate-image list vs upload top-level).

Run:  python -m unittest flow_bridge.tests.test_bridge -v
"""

from __future__ import annotations

import base64
import unittest

from flow_bridge.client import (
    FlowError,
    FlowExecClient,
    _find_first,
    _is_stale_captcha,
    _media_summary,
)
from flow_bridge.envelope import (
    ASPECT_PORTRAIT,
    MODE_AI,
    MODE_UPLOAD,
    EnvelopeError,
    aspect_from_platform,
    extract_motion_prompt,
    project,
    sanitize_image_prompt,
)

COMPILED = {
    "identity": {"engine": "GOOGLE_FLOW", "platform": "TikTok Shop Malaysia", "scene_id": "sc-1"},
    "parsed": {"hook": "h", "cta": "c"},
    "product": {"product_truth_lock": "BOSMAX Serum 5ML roll-on.", "scale_lock": "EXACTLY lip balm size."},
    "angle": {"scene_context_seed": "Dalam kereta, sapu pada pergelangan."},
    "storyboard": {
        "master_storyboard": "fallback board",
        "block_script_json": [{"block": 1, "flow_prompt": "Push-in on wrist apply, product sharp."}],
    },
}


class TestEnvelope(unittest.TestCase):
    def test_shape_is_exactly_contract_5(self):
        env = project(COMPILED)
        d = env.to_dict()
        # exact top-level keys, nothing more, nothing less
        self.assertEqual(set(d), {"prompt", "aspect_ratio", "user_paygate_tier", "start_frame"})
        # project_id and scene_id must NOT leak into the wire envelope (oneshot mints them)
        self.assertNotIn("project_id", d)
        self.assertNotIn("scene_id", d)

    def test_infer_ai_when_no_product_photo(self):
        env = project(COMPILED)
        self.assertEqual(env.start_frame.mode, MODE_AI)
        self.assertIn("kereta", env.start_frame.image_prompt)        # scene seed
        self.assertIn("BOSMAX Serum 5ML", env.start_frame.image_prompt)  # product truth
        self.assertEqual(set(env.to_dict()["start_frame"]), {"mode", "image_prompt"})

    def test_upload_mode_with_bytes(self):
        b64 = base64.b64encode(b"PNG").decode()
        env = project(COMPILED, mode=MODE_UPLOAD, image_base64=b64)
        sf = env.to_dict()["start_frame"]
        self.assertEqual(sf["mode"], MODE_UPLOAD)
        self.assertEqual(sf["image_base64"], b64)
        self.assertEqual(sf["mime_type"], "image/png")
        self.assertNotIn("image_prompt", sf)

    def test_upload_mode_without_bytes_fails_loud(self):
        with self.assertRaises(EnvelopeError):
            project(COMPILED, mode=MODE_UPLOAD)

    def test_no_prompt_fails_loud(self):
        bad = {"storyboard": {"block_script_json": [{"block": 1}]}}
        with self.assertRaises(EnvelopeError):
            project(bad)

    def test_aspect_portrait_for_social(self):
        self.assertEqual(aspect_from_platform("TikTok Shop MY"), ASPECT_PORTRAIT)
        self.assertEqual(aspect_from_platform("YouTube Shorts"), ASPECT_PORTRAIT)
        self.assertEqual(aspect_from_platform(None), ASPECT_PORTRAIT)
        self.assertEqual(aspect_from_platform("x", explicit="VIDEO_ASPECT_RATIO_LANDSCAPE"),
                         "VIDEO_ASPECT_RATIO_LANDSCAPE")

    def test_prompt_key_fallback_order(self):
        t = {"storyboard": {"block_script_json": [{"google_flow_prompt": "A", "prompt": "B"}]}}
        self.assertEqual(extract_motion_prompt(t), "A")  # higher-priority key wins

    def test_master_storyboard_fallback(self):
        t = {"storyboard": {"master_storyboard": "only board", "block_script_json": []}}
        self.assertEqual(extract_motion_prompt(t), "only board")

    def test_tier_passthrough(self):
        env = project(COMPILED, user_paygate_tier="PAYGATE_TIER_TWO")
        self.assertEqual(env.to_dict()["user_paygate_tier"], "PAYGATE_TIER_TWO")

    def test_compiler_9_sections_preferred_over_final_text(self):
        # real pipeline shape: clean 9-section body must win over final_prompt_text,
        # which carries the forbidden orchestration wrapper (prompt_set_count / SET 1)
        t = {
            "storyboard": {"block_script_json": [{"block_visual_action": "ignore me"}]},
            "compiler": {
                "final_prompt_text": "SINGLE PROMPT\nprompt_set_count: 1\nSET 1 - 8 SECONDS\n...",
                "final_prompt_blocks": [{"final_prompt_9_sections": [
                    {"section_heading": "ROLE & OBJECTIVE", "section_text": "Build an 8s Flow video."},
                    {"section_heading": "VISUAL STORY", "section_text": "Push-in on wrist apply."},
                ]}],
            },
        }
        out = extract_motion_prompt(t)
        self.assertIn("ROLE & OBJECTIVE", out)
        self.assertIn("Push-in on wrist apply", out)
        self.assertNotIn("prompt_set_count", out)   # no metadata leak (BOSMAX fail-closed)
        self.assertNotIn("SINGLE PROMPT", out)

    def test_block_visual_action_path(self):
        t = {"storyboard": {"block_script_json": [
            {"block_visual_action": "Man applies roll-on in car.", "block_dialogue_or_copy": "Senang sapu."}]}}
        out = extract_motion_prompt(t)
        self.assertIn("Man applies roll-on", out)
        self.assertIn('Spoken: "Senang sapu."', out)


class TestMediaSummary(unittest.TestCase):
    def test_generate_image_list_shape(self):
        resp = {"media": [{"name": "uuid-gen",
                           "image": {"generatedImage": {"fifeUrl": "https://f", "mediaId": "uuid-gen"}}}]}
        out = _media_summary(resp)
        self.assertEqual(out["media_id"], "uuid-gen")
        self.assertEqual(out["fife_url"], "https://f")

    def test_upload_top_level_media_id(self):
        # the shape that the old code missed (agent/api/flow.py:440,470)
        resp = {"media_id": "uuid-upl", "local_file_path": "/tmp/x.png", "raw": {}}
        out = _media_summary(resp)
        self.assertEqual(out["media_id"], "uuid-upl")
        self.assertEqual(out["local_path"], "/tmp/x.png")

    def test_no_media_id_fails_loud(self):
        with self.assertRaises(FlowError):
            _media_summary({"raw": {}})


class TestFindFirst(unittest.TestCase):
    def test_deep_trpc_create_project_envelope(self):
        # the exact shape the LIVE create-project-raw returned (deep tRPC wrap)
        resp = {"id": "x", "status": 200, "data": {"result": {"data": {"json": {
            "result": {"projectId": "0a751ddd", "projectInfo": {"projectTitle": "t"}},
            "status": 200}}}}}
        self.assertEqual(_find_first(resp, "projectId"), "0a751ddd")

    def test_top_level_and_missing(self):
        self.assertEqual(_find_first({"projectId": "p"}, "projectId"), "p")
        self.assertIsNone(_find_first({"a": {"b": 1}}, "projectId"))


class TestSanitizeImagePrompt(unittest.TestCase):
    QISTINA = (
        "Create a photorealistic avatar reference image. Identity: Qistina, "
        "Code: BOS_F_QISTINA_10. Demographic: Female. Role: Event Lifestyle. "
        "Camera framing: Waist-up, clear face."
    )

    def test_strips_labels_code_and_adds_guard(self):
        out = sanitize_image_prompt(self.QISTINA, avatar_code="BOS_F_QISTINA_10")
        self.assertNotIn("BOS_F_QISTINA_10", out)        # internal code never in pixels
        self.assertNotIn("Identity:", out)
        self.assertNotIn("Code:", out)
        self.assertNotIn("Camera framing:", out)
        self.assertIn("No added text overlays", out)      # targeted no-overlay guard

    def test_strips_internal_code_even_without_explicit_arg(self):
        out = sanitize_image_prompt("Portrait of a woman. Code: MWT_F_NORA_2.")
        self.assertNotIn("MWT_F_NORA_2", out)

    def test_keeps_product_label_text(self):
        # the crucial refinement over a blanket 'no text/no labels' guard:
        # a product's own printed wordmark must still render
        p = ("Photo of BOSMAX Serum bottle, white BOSMAX HERBS wordmark, "
             "Herbal Oil Roll On label visible.")
        out = sanitize_image_prompt(p)
        self.assertIn("BOSMAX HERBS wordmark", out)
        self.assertIn("Herbal Oil Roll On label", out)

    def test_idempotent_guard(self):
        once = sanitize_image_prompt("A cat.")
        twice = sanitize_image_prompt(once)
        self.assertEqual(once.lower().count("no added text"), 1)
        self.assertEqual(twice.lower().count("no added text"), 1)

    def test_empty_passthrough(self):
        self.assertEqual(sanitize_image_prompt(""), "")
        self.assertIsNone(sanitize_image_prompt(None))


class TestCaptchaRecovery(unittest.TestCase):
    def _client(self):
        c = FlowExecClient(base="http://test")
        c.reloads = 0

        def fake_request(method, path, body=None, timeout=None):
            if "reload-flow-tab" in path:
                c.reloads += 1
                return {"ok": True}
            raise AssertionError(f"unexpected request {path}")

        c._request = fake_request
        return c

    def test_markers(self):
        self.assertTrue(_is_stale_captcha("CAPTCHA_FAILED: Cannot access contents of the page"))
        self.assertTrue(_is_stale_captcha("ERR_MESSAGE_RESPONSE_TIMEOUT"))
        self.assertFalse(_is_stale_captcha("No model for tier=PAYGATE_TIER_NOT_PAID"))

    def test_reloads_then_succeeds(self):
        c = self._client()
        n = {"i": 0}

        def flaky():
            n["i"] += 1
            if n["i"] < 3:
                raise FlowError(403, "CAPTCHA_FAILED: Cannot access contents of the page")
            return {"media_id": "ok"}

        out = c.with_captcha_recovery(flaky, wait=0)
        self.assertEqual(out["media_id"], "ok")
        self.assertEqual(n["i"], 3)
        self.assertEqual(c.reloads, 2)  # reloaded before each retry

    def test_non_captcha_error_propagates_without_reload(self):
        c = self._client()

        def boom():
            raise FlowError(500, "No model for tier=PAYGATE_TIER_NOT_PAID")

        with self.assertRaises(FlowError):
            c.with_captcha_recovery(boom, wait=0)
        self.assertEqual(c.reloads, 0)

    def test_exhausted_reraises(self):
        c = self._client()

        def always():
            raise FlowError(403, "CAPTCHA_FAILED: must request permission")

        with self.assertRaises(FlowError):
            c.with_captcha_recovery(always, max_retries=2, wait=0)
        self.assertEqual(c.reloads, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
