"""
Prove the OTAK -> TANGAN seam end-to-end WITHOUT burning video (freemium-safe).

Per contract section 7: envelope -> create project -> start frame
(generate-image OR upload) -> media_id, then STOP before generate-video.
Only the final generate-video step needs a paid (Pro/Ultra) account.

Usage:
  # dry: just project a BOSMAX template -> envelope JSON, no network
  python -m flow_bridge.prove_seam --template path/to/compiled_template.json --dry

  # live freemium: project -> POST to TANGAN -> get a real start-frame media_id
  FLOW_API_BASE=http://127.0.0.1:8100 \
  python -m flow_bridge.prove_seam --template path/to/compiled_template.json

  # force AI frame even if the template implies upload
  python -m flow_bridge.prove_seam --template t.json --mode ai
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path

from .client import FlowError, FlowExecClient
from .envelope import EnvelopeError, project


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Prove OTAK->TANGAN seam (freemium-safe).")
    ap.add_argument("--template", required=True, help="compiled BOSMAX video template JSON")
    ap.add_argument("--tier", default="PAYGATE_TIER_ONE")
    ap.add_argument("--mode", choices=["ai", "upload"], default=None, help="override start-frame mode")
    ap.add_argument("--image", default=None, help="product photo file (required if mode=upload)")
    ap.add_argument("--aspect", default=None, help="override aspect_ratio")
    ap.add_argument("--dry", action="store_true", help="project only; no network")
    ap.add_argument("--base", default=None, help="override FLOW_API_BASE")
    args = ap.parse_args(argv)

    try:
        template = json.loads(Path(args.template).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[fail] cannot read template: {e}", file=sys.stderr)
        return 2

    image_b64 = None
    mime = "image/png"
    if args.image:
        image_b64 = base64.b64encode(Path(args.image).read_bytes()).decode()
        mime = mimetypes.guess_type(args.image)[0] or "image/png"

    try:
        env = project(template, user_paygate_tier=args.tier, aspect_ratio=args.aspect,
                      mode=args.mode, image_base64=image_b64, mime_type=mime)
    except EnvelopeError as e:
        print(f"[fail] projection: {e}", file=sys.stderr)
        return 3

    print("[ok] envelope projected:")
    print(json.dumps(env.to_dict(), indent=2, ensure_ascii=False)[:1200])
    print(f"     scene_id={env.scene_id}  meta={env.meta}")

    if args.dry:
        print("[dry] stopping before network. Seam shape proven.")
        return 0

    client = FlowExecClient(base=args.base or "")
    print(f"[..] TANGAN base = {client.base}")

    # precondition gate (contract section 2)
    ok, reasons = client.ready()
    if not ok:
        print(f"[fail] not ready: {'; '.join(reasons)}", file=sys.stderr)
        return 4
    paid, tier = client.is_paid()
    print(f"[ok] ready. tier={tier} ({'PAID' if paid else 'FREEMIUM — image only, no video'})")

    try:
        pid = client.create_project(f"seam-proof {env.scene_id}")
        print(f"[ok] project: {pid}")
        sf = env.start_frame
        if sf.mode == "upload":
            frame = client.with_captcha_recovery(
                client.upload_image_base64, sf.image_base64, pid, mime_type=sf.mime_type)
        else:
            frame = client.with_captcha_recovery(
                client.generate_image, sf.image_prompt or env.prompt, pid,
                user_paygate_tier=args.tier)
        print(f"[ok] start frame media_id = {frame['media_id']}")
        if frame.get("fife_url"):
            print(f"     fifeUrl = {frame['fife_url']}")
    except FlowError as e:
        print(f"[fail] seam: {e}", file=sys.stderr)
        return 5

    print("[done] Seam proven up to start-frame media_id.")
    print("       generate-video deliberately NOT called (needs Pro/Ultra). "
          "When Pro is live, the TANGAN /shoot-oneshot takes this exact envelope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
