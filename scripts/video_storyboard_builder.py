from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from video_block_plan import build_plan  # type: ignore[import]
from video_template_parser import build_canonical_template, load_input  # type: ignore[import]


class StoryboardError(RuntimeError):
    """Raised when storyboard construction cannot continue safely."""


def _load_template(path: Path) -> dict[str, Any]:
    payload = load_input(path)
    if "identity" in payload and "duration" in payload and "parsed" in payload:
        return payload
    return build_canonical_template(payload, path)


def _word_count(text: str) -> int:
    return len([token for token in text.split() if token.strip()])


def _split_sentences(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in text.replace("\n", " ").split(".")]
    return [chunk for chunk in chunks if chunk]


def _chunk_body(text: str, parts: int) -> list[str]:
    if parts <= 0:
        return []
    sentences = _split_sentences(text)
    if not text.strip():
        return [""] * parts
    if len(sentences) < parts:
        words = text.split()
        chunk_size, remainder = divmod(len(words), parts)
        groups: list[str] = []
        start = 0
        for index in range(parts):
            stop = start + chunk_size + (1 if index < remainder else 0)
            groups.append(" ".join(words[start:stop]).strip())
            start = stop
        return groups
    groups = [""] * parts
    index = 0
    for sentence in sentences:
        current = groups[index]
        groups[index] = f"{current} {sentence}".strip() if current else sentence
        if index < parts - 1:
            index += 1
    return groups


def _join_parts(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip()).strip()


def _join_spoken(*parts: str) -> str:
    """Join spoken segments with proper sentence boundaries so a body chunk and
    the CTA do not run together (e.g. '...lega Tap tengok' -> '...lega. Tap tengok')."""
    cleaned = [part.strip() for part in parts if part and part.strip()]
    out = ""
    for part in cleaned:
        if not out:
            out = part
            continue
        if out[-1] not in ".?!,":
            out += "."
        out += f" {part}"
    return out.strip()


def _derive_storyline(template: dict[str, Any]) -> str:
    parsed = template["parsed"]
    storyline = _join_parts(parsed.get("hook", ""), parsed.get("body", ""), parsed.get("cta", ""))
    if not storyline:
        storyline = template["input"].get("raw_prompt_seed", "")
    return storyline.strip()


def _derive_storyboard_summary(template: dict[str, Any], block_plan: list[int]) -> str:
    product_lane = template["identity"]["product_lane"]
    mode = template["identity"]["mode"]
    engine = template["identity"]["engine"]
    storyline = template["storyboard"]["master_storyline"]
    blocks = " + ".join(f"{seconds}s" for seconds in block_plan)
    return (
        f"{product_lane} {mode} runtime on {engine}: {storyline} "
        f"resolved across {len(block_plan)} block(s) [{blocks}] with continuity preserved."
    )


def _derive_arc(block_count: int) -> list[str]:
    if block_count == 1:
        return ["HOOK_BODY_CTA"]
    if block_count == 2:
        return ["HOOK_PAIN_FRICTION", "RELIEF_CTA"]
    arc = ["HOOK_PAIN"]
    for _ in range(block_count - 2):
        arc.append("PROOF_DEVELOPMENT")
    arc.append("RELIEF_CTA")
    return arc


def _build_dialogue_segments(template: dict[str, Any], block_count: int) -> list[str]:
    parsed = template["parsed"]
    hook = parsed.get("hook", "")
    body = parsed.get("body", "")
    cta = parsed.get("cta", "")
    if block_count == 1:
        return [_join_spoken(hook, body, cta)]

    body_chunks = _chunk_body(body, block_count)
    segments: list[str] = []
    for index in range(block_count):
        if index == 0:
            segments.append(_join_spoken(hook, body_chunks[0]))
            continue
        if index == block_count - 1:
            tail_source = body_chunks[index] if index < len(body_chunks) else ""
            segments.append(_join_spoken(tail_source, cta))
            continue
        middle_source = body_chunks[index] if index < len(body_chunks) else ""
        segments.append(middle_source.strip())
    return [segment.strip() for segment in segments]


def build_storyboard(template: dict[str, Any]) -> dict[str, Any]:
    duration = template["duration"]
    identity = template["identity"]
    parsed = template["parsed"]
    declared_plan = [int(item) for item in duration["block_plan"]]
    planner = build_plan(
        engine_id=identity["engine"],
        total_duration_seconds=int(duration["duration_seconds"]),
        execution_mode=duration["prompt_execution_mode"],
    )
    planner_plan = [int(item) for item in planner["block_durations_seconds"]]
    if declared_plan != planner_plan:
        raise StoryboardError(
            f"Declared block plan {declared_plan} does not match BOSMAX planner {planner_plan}"
        )

    master_storyline = template["storyboard"].get("master_storyline") or _derive_storyline(template)
    if duration["block_mode"] == "MULTI_BLOCK" and not master_storyline:
        raise StoryboardError("Multi-block templates require a master storyline before compilation")

    template["storyboard"]["master_storyline"] = master_storyline
    template["storyboard"]["master_storyboard"] = (
        template["storyboard"].get("master_storyboard")
        or _derive_storyboard_summary(template, declared_plan)
    )
    template["storyboard"]["narrative_arc"] = (
        template["storyboard"].get("narrative_arc") or _derive_arc(len(declared_plan))
    )
    product_lock = str(template["input"].get("product_truth_lock") or "").strip()
    scale_lock = str(template["input"].get("scale_lock") or "").strip()
    product_ref = template["input"].get("product_truth_ref") or identity["product_lane"]
    template["storyboard"]["character_continuity_lock"] = (
        template["storyboard"].get("character_continuity_lock")
        or "Keep the same presenter identity, age range, wardrobe tone, and hand dominance across all blocks."
    )
    template["storyboard"]["product_continuity_lock"] = (
        template["storyboard"].get("product_continuity_lock")
        or " ".join(
            part
            for part in [
                product_lock,
                scale_lock,
                "" if product_lock else f"Keep product truth anchored to {product_ref}; label, scale, packaging color, and handling orientation must stay stable.",
            ]
            if part
        )
    )
    template["storyboard"]["setting_camera_lock"] = (
        template["storyboard"].get("setting_camera_lock")
        or "Maintain the same commercial setting, camera family, and lighting direction unless a planned proof cut is declared."
    )

    dialogues = _build_dialogue_segments(template, len(declared_plan))
    block_scripts: list[dict[str, Any]] = []
    previous_end_state = ""
    for plan_block, dialogue in zip(planner["blocks"], dialogues):
        index = int(plan_block["block_index"])
        role = str(plan_block.get("block_role") or template["storyboard"]["narrative_arc"][index - 1])
        visual_seed = template["input"].get("visual_seed", "")
        block_id = f"{template['template_id']}_BLOCK_{index:02d}"
        start_state = (
            previous_end_state
            if previous_end_state
            else f"Open on the first proof beat for {identity['product_lane']} with the same presenter and product in hand."
        )
        end_state = (
            f"End on a clear product-facing frame with {role.lower()} tension carried into the next beat."
            if index < len(declared_plan)
            else "End on a clean CTA close with product hero visibility preserved."
        )
        continuity_anchor = (
            "Resume from the exact prior frame's body angle, prop position, and spoken thread."
            if index > 1
            else "Establish the opening continuity anchor from zero."
        )
        block_scripts.append(
            {
                "block_id": block_id,
                "block_index": index,
                "block_duration": plan_block["block_duration_seconds"],
                "block_narrative_function": role,
                "block_visual_action": _join_parts(
                    visual_seed,
                    f"Role focus: {role.lower().replace('_', ' ')}.",
                ),
                "block_dialogue_or_copy": dialogue,
                "block_dialogue_word_count": _word_count(dialogue),
                "block_wps_budget": dict(plan_block.get("dialogue_budget") or {}),
                "block_start_state": start_state,
                "block_end_state": end_state,
                "block_continuity_anchor": continuity_anchor,
                "block_allowed_changes": [
                    "Hand gesture refinement",
                    "Small camera reframing for proof emphasis",
                ],
                "block_forbidden_changes": [
                    "Identity reset",
                    "Packaging scale drift",
                    "Scene reset",
                    "Unplanned overlay text",
                ],
                "requires_frame_bridge": bool(plan_block.get("requires_frame_bridge")),
                "requires_previous_clip_final_second": bool(plan_block.get("requires_previous_clip_final_second")),
                "previous_clip_final_second_state": previous_end_state if index > 1 else "",
                "bridge_in_required": bool(plan_block.get("bridge_in_required")),
                "bridge_out_required": bool(plan_block.get("bridge_out_required")),
            }
        )
        previous_end_state = end_state

    if duration["block_mode"] == "MULTI_BLOCK" and not template["storyboard"]["master_storyboard"]:
        raise StoryboardError("Multi-block templates require a master storyboard before compilation")

    template["storyboard"]["block_script_json"] = block_scripts
    parsed["parsed_brief"] = parsed.get("parsed_brief") or master_storyline
    template["qa"]["generated_by"] = "scripts/video_storyboard_builder.py"
    return template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic BOSMAX master storyboard and block script JSON."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template = _load_template(Path(args.input))
    built = build_storyboard(template)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() in {".yaml", ".yml"} or args.format == "yaml":
            output_path.write_text(
                yaml.safe_dump(built, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
        else:
            output_path.write_text(
                json.dumps(built, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        print(output_path)
        return

    if args.format == "yaml":
        print(yaml.safe_dump(built, sort_keys=False, allow_unicode=True))
        return
    print(json.dumps(built, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
