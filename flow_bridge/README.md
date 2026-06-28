# flow_bridge — OTAK → TANGAN seam (Google Flow video)

The **OTAK side** of the two-repo system. It turns a BOSMAX compiled video template
into the single JSON envelope the **TANGAN** service (`_ref_flowkit` FastAPI on
`:8100`) executes against Google Flow.

```
[ BOSMAX OTAK ]──flow_bridge──▶ envelope(JSON) ──HTTP──▶ [ TANGAN :8100 ] ──▶ Google Flow
```

- **Two repos, zero git coupling.** Talks HTTP only. Base URL is config-driven via
  `FLOW_API_BASE` (default `http://127.0.0.1:8100`) — swap one env var for cloud.
- **Pure stdlib.** No third-party deps, no BOSMAX import. Consumes a plain dict.
- Authoritative seam spec: `_ref_flowkit/docs/INTEGRATION_CONTRACT.md` (sections 1–7).

## Files
| File | Job |
|---|---|
| `envelope.py` | `project(template, ...)` → contract-§5 `Envelope`. Fail-loud if no motion prompt. |
| `client.py` | `FlowExecClient` — thin HTTP to every TANGAN endpoint + `/shoot-oneshot` (async). |
| `prove_seam.py` | freemium-safe CLI: envelope → project → frame `media_id`, stops before video. |

## The envelope (contract §5)
```json
{
  "prompt": "<motion prompt from storyboard.block_script_json>",
  "aspect_ratio": "VIDEO_ASPECT_RATIO_PORTRAIT",
  "user_paygate_tier": "PAYGATE_TIER_ONE",
  "start_frame": { "mode": "ai|upload", "image_prompt": "...", "image_base64": "...", "mime_type": "image/png" }
}
```
- `prompt` ← first `block_script_json` Flow prompt (probes `google_flow_prompt`/`flow_prompt`/… ).
- `aspect_ratio` ← derived from platform (TikTok/Shorts/Reels → portrait), overridable.
- `start_frame.mode` ← inferred from asset roles: product photo present → `upload`
  (the BOSMAX "product is the anchor" rule), else `ai` (scene brief composed from
  angle seed + product truth + scale lock).

## Quick use
```python
from flow_bridge import project, FlowExecClient
env = project(compiled_template, user_paygate_tier="PAYGATE_TIER_ONE")
client = FlowExecClient()              # FLOW_API_BASE env, default :8100
ok, why = client.ready()               # check 3 preconditions first
# later (once TANGAN /shoot-oneshot is built + Pro account live):
# job = client.shoot_oneshot(env.to_dict()); client.poll_job(job["job_id"])
```

## Prove the seam (freemium today; Pro burn tomorrow)
Two real fixtures ship in `tests/`: `sample_compiled_flow_real.json` (a real
BOSMAX Serum / GOOGLE_FLOW compiled template from the production pipeline) and
`sample_envelope_real.json` (its projected AI-frame envelope).

```bash
# shape only, no network (proves projection)
python -m flow_bridge.prove_seam --template flow_bridge/tests/sample_compiled_flow_real.json --dry

# AI start-frame path — live, freemium-safe (generate-image is 0 credits; stops before video)
FLOW_API_BASE=http://127.0.0.1:8100 \
  python -m flow_bridge.prove_seam --template flow_bridge/tests/sample_compiled_flow_real.json

# UPLOAD start-frame path — real product photo already in the repo
FLOW_API_BASE=http://127.0.0.1:8100 \
  python -m flow_bridge.prove_seam \
    --template flow_bridge/tests/sample_compiled_flow_real.json \
    --mode upload --image reference_images/bosmax/bosmax_serum_5ml_primary.jpg
```
Both paths run end-to-end up to the start-frame `media_id` on freemium; only the
final `generate-video` needs a paid (Pro/Ultra) account.

## Status
- ✅ envelope projection (verified: AI infer, upload, fail-loud) — `tests/sample_compiled_flow.json`
- ✅ HTTP client for all existing TANGAN endpoints + precondition gate
- ⏳ waiting on TANGAN `/shoot-oneshot` + `/job/{id}` (contract §4) to wire the async one-shot
- ⏳ real `generate-video` burn needs a Pro/Ultra account
