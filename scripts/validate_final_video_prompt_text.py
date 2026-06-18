"""
validate_final_video_prompt_text.py
BOSMAX Final Video Prompt — RAW TEXT quality gate.

Deterministic post-hoc scanner over the *raw* 9-section video prompt TEXT that
is actually handed to the engine (or pasted into chat) — independent of which
lane produced it. The video_template_compiler_runtime lane already enforces
these gates on its structured templates, but a prompt authored by the chat-lane
LLM never passes through that compiler. This scanner closes that gap: it scans
the delivered text itself, so the four prompt-quality defects are caught even
when the deterministic compiler was bypassed.

Defects caught:
  A. METADATA LEAK   — internal orchestration / budget scaffolding leaked into
                       the engine-facing prompt body (output_mode=, block_source=,
                       "Runtime plan", "Do not use two equal 8-second blocks", ...).
  B. UNDERFILL       — spoken dialogue below the WPS corridor minimum for its
                       duration → dead air → engine fills it with hallucinated
                       filler / glitch. Blocking, REWRITE_REQUIRED.
  C. CODE-SWITCH     — English / internal storyboard labels ("family shelf",
                       "shelf cue", "b-roll", ...) inside a BM spoken line.
  D. VO/LIP CONFLICT — "voiceover only" declared alongside a presenter / lip-sync
                       cue (talking head, speaks to camera, mouth movement). A
                       self-consistent product-only voiceover is NOT flagged here;
                       the talking-vs-faceless routing decision is enforced
                       upstream by presenter_route in the parser/compiler.

Single source of truth: the metadata and code-switch pattern lists, and the
WPS corridor, are imported from the same artefacts the compiler uses — this
scanner never re-defines them.

Usage:
    python scripts/validate_final_video_prompt_text.py <prompt.txt> [--language BM] [--pace BRISK_UGC]
    python scripts/validate_final_video_prompt_text.py            # runs self-test
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# Force UTF-8 stdout so status markers do not crash on cp1252 Windows consoles.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (ValueError, OSError):
        pass

# Running this file puts scripts/ on sys.path[0]; import the compiler's pattern
# lists directly so there is one source of truth for what counts as a leak.
sys.path.insert(0, str(Path(__file__).parent))
from video_prompt_compiler import (  # type: ignore[import]  # noqa: E402
    BM_DIALOGUE_LEAK_PATTERNS,
    PROMPT_SURFACE_METADATA_PATTERNS,
)

CORRIDOR_PATH = (
    Path(__file__).parent.parent / "registries" / "dialogue_budget_corridor.yaml"
)

# Presenter / lip-sync cues. Their presence means the clip shows a talking face,
# so "voiceover only" is a contradiction (the face would have no synced speech).
PRESENTER_CUE_PATTERNS = [
    r"lip[\s-]?sync",
    r"\bpresenter\b",
    r"speaks?\s+to\s+camera",
    r"talking[\s-]?head",
    r"on[\s-]?camera\s+(?:host|presenter|talent|spokesperson)",
    r"mouth\s+(?:movement|moves|moving)",
    r"\bspokesperson\b",
]

VOICEOVER_ONLY_PATTERN = r"voice[\s-]?over\s+only"

# Smart and straight quote pairs used for spoken lines.
_QUOTE_RE = re.compile(r"[“\"]([^“”\"]+)[”\"]")
# A SET header is "SET <n>" followed by a dash/colon or end-of-line — NOT
# "SET 1 of a two-prompt..." narration that happens to start a wrapped line.
_SET_HEADER_RE = re.compile(r"(?im)^\s*SET\s+(\d+)\b(?=\s*(?:[—–:-]|$))")
_SECTION_HEADER_RE = re.compile(r"(?im)^\s*(\d+)\.\s+([A-Z][A-Z0-9 /&_]+?)\s*$")
_DURATION_RE = re.compile(r"(\d+)\s*-?\s*second", re.IGNORECASE)


def _load_corridor() -> list[dict]:
    payload = yaml.safe_load(CORRIDOR_PATH.read_text(encoding="utf-8"))
    return list(payload.get("corridors", []))


def _corridor_row(
    corridors: list[dict], language: str, pace: str, duration: int
) -> dict | None:
    for row in corridors:
        if (
            str(row.get("language", "")).upper() == language.upper()
            and str(row.get("pace_class", "")).upper() == pace.upper()
            and int(row.get("duration_seconds", -1)) == duration
        ):
            return row
    return None


def _word_count(text: str) -> int:
    return len([tok for tok in text.split() if tok.strip()])


def _parse_clip_duration(set_text: str) -> int | None:
    """The clip duration is the "N-second <video>" in the engine line, NOT the
    "16-second multi-prompt sequence" reference describing the whole chain."""
    for match in _DURATION_RE.finditer(set_text):
        tail = set_text[match.end() : match.end() + 28].lower()
        if "sequence" in tail or "multi-prompt" in tail or "multiprompt" in tail:
            continue
        return int(match.group(1))
    return None


def _split_sets(text: str) -> list[tuple[str, str]]:
    """Return [(set_label, set_text), ...]. If no SET headers, one synthetic set."""
    matches = list(_SET_HEADER_RE.finditer(text))
    if not matches:
        return [("SET 1", text)]
    sets: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sets.append((f"SET {match.group(1)}", text[start:end]))
    return sets


def _split_sections(set_text: str) -> dict[str, str]:
    """Map section title (upper) -> body text within one set."""
    matches = list(_SECTION_HEADER_RE.finditer(set_text))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        title = match.group(2).strip().upper()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(set_text)
        sections[title] = set_text[start:end].strip()
    return sections


def _find_dialogue_section(sections: dict[str, str]) -> str | None:
    for title, body in sections.items():
        if any(key in title for key in ("SPOKEN", "DIALOGUE", "VOICE")):
            return body
    return None


def _extract_spoken_words(dialogue_body: str) -> str:
    """Spoken words = quoted spans. Falls back to lines that are not the
    'Voiceover only' label or the 'Delivery:' direction line."""
    quoted = _QUOTE_RE.findall(dialogue_body)
    if quoted:
        return " ".join(q.strip() for q in quoted)
    spoken: list[str] = []
    for line in dialogue_body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        low = stripped.lower()
        if low.startswith(("delivery", "voiceover", "voice-over", "voice over")):
            continue
        spoken.append(stripped)
    return " ".join(spoken)


def scan_prompt_text(
    text: str, language: str = "BM", pace: str = "BRISK_UGC"
) -> list[str]:
    """Return a list of blocking findings. Empty list == clean."""
    corridors = _load_corridor()
    findings: list[str] = []

    for set_label, set_text in _split_sets(text):
        # A. metadata / orchestration leak anywhere in the set body
        for pattern in PROMPT_SURFACE_METADATA_PATTERNS:
            if re.search(pattern, set_text, flags=re.IGNORECASE):
                findings.append(
                    f"{set_label}: metadata/orchestration leak in prompt body "
                    f"(pattern: {pattern})"
                )

        sections = _split_sections(set_text)
        dialogue_body = _find_dialogue_section(sections)
        spoken = _extract_spoken_words(dialogue_body) if dialogue_body else ""

        # B. underfill vs WPS corridor minimum
        duration = _parse_clip_duration(set_text)
        if dialogue_body and spoken and duration is not None:
            row = _corridor_row(corridors, language, pace, duration)
            if row is not None:
                words = _word_count(spoken)
                minimum = int(row["minimum_words"])
                if words < minimum:
                    findings.append(
                        f"{set_label}: UNDERFILLED dialogue — {words} words for "
                        f"{duration}s {language}/{pace} (minimum {minimum}). "
                        f"REWRITE_REQUIRED: dead air invites hallucinated filler."
                    )

        # C. code-switch / internal label inside a BM spoken line
        if language.upper() == "BM" and spoken:
            for pattern in BM_DIALOGUE_LEAK_PATTERNS:
                if re.search(pattern, spoken, flags=re.IGNORECASE):
                    findings.append(
                        f"{set_label}: BM spoken line contains an internal/English "
                        f"code-switch token (pattern: {pattern})."
                    )

        # D. voiceover-only declared alongside a presenter / lip-sync cue
        if re.search(VOICEOVER_ONLY_PATTERN, set_text, flags=re.IGNORECASE):
            cues = [
                p
                for p in PRESENTER_CUE_PATTERNS
                if re.search(p, set_text, flags=re.IGNORECASE)
            ]
            if cues:
                findings.append(
                    f"{set_label}: 'voiceover only' conflicts with a presenter/"
                    f"lip-sync cue ({cues[0]}). Resolve presenter_route: a talking "
                    f"face needs synced speech, not voiceover."
                )

    return findings


# ──────────────────────────────────────────────────────────────────────────────
# SELF-TEST — the operator's exact failing case must BLOCK; a clean prompt PASSes
# ──────────────────────────────────────────────────────────────────────────────

# Faithful reconstruction of the leaked GROK 16s [10,6] output (defects A/B/C).
_BAD_SAMPLE = """
SET 1 — GROK 10s — 9 SECTION PROMPT
1. ENGINE / FORMAT
Create a 10-second GROK product-only video for TikTok Shop Malaysia. This is
SET 1 of a two-prompt 16-second multi-prompt sequence. Runtime plan is [10,6].
Do not compile as one 16-second video. Do not use two equal 8-second blocks.
output_mode=MULTI_PROMPT_SET. block_source=BOSMAX_GROK_BLOCK_01.
7. SPOKEN MALAY DIALOGUE
Voiceover only, natural Malay spoken delivery:
“Ruang rumah nampak tersusun. Letak atas rak keluarga pun nampak kemas, senang capai bila perlu.”
Delivery: calm Malay household tone, warm, practical, not exaggerated.

SET 2 — GROK 6s CONTINUATION — 9 SECTION PROMPT
1. ENGINE / FORMAT
Create a 6-second GROK continuation video for TikTok Shop Malaysia. This is
SET 2 of the same two-prompt 16-second multi-prompt sequence.
7. SPOKEN MALAY DIALOGUE
Voiceover only, natural Malay spoken delivery:
“Family shelf nampak kemas. Tap tengok harga sekarang.”
Delivery: direct, calm, TikTok Shop native, practical.
"""

# A clean equivalent: no metadata, corridor-filled BM dialogue, no code-switch.
_GOOD_SAMPLE = """
SET 1 — GROK 10s — 9 SECTION PROMPT
1. ENGINE / FORMAT
Build a complete 10-second GROK commercial video for TikTok Shop Malaysia,
covering the hook and pain beat of a continuous two-part video.
7. VOICE & DELIVERY
Presenter speaks in natural Malay, lip-sync locked to camera:
“Rumah berselerak buat kepala serabut betul, kan? Barang bersepah merata sampai tetamu datang pun kita rasa malu sebab memang langsung tak sempat nak kemas rumah ni.”
Delivery: warm, brisk Malay household tone, practical, believable.

SET 2 — GROK 6s CONTINUATION — 9 SECTION PROMPT
1. ENGINE / FORMAT
Continue the final 6-second beat of the same two-part video.
7. VOICE & DELIVERY
Presenter continues in natural Malay, lip-sync locked:
“Sekarang semua dah tersusun kemas, rumah nampak lega terus. Jom, tap tengok harga sekarang, boss.”
Delivery: confident, calm, TikTok Shop native close.
"""


def _self_test() -> int:
    print("=" * 70)
    print("SELF-TEST: validate_final_video_prompt_text")
    print("=" * 70)

    bad = scan_prompt_text(_BAD_SAMPLE, language="BM", pace="BRISK_UGC")
    print(f"\n[BAD SAMPLE] expected to BLOCK — {len(bad)} finding(s):")
    for f in bad:
        print(f"  ❌ {f}")

    # The leaked output must trip: metadata leak (×2 sets), underfill (×2 sets),
    # code-switch (SET 2). Assert each defect class is represented.
    joined = " ".join(bad).lower()
    checks = {
        "metadata leak": "metadata/orchestration leak" in joined,
        "underfill SET 1": "set 1: underfilled" in joined,
        "underfill SET 2": "set 2: underfilled" in joined,
        "code-switch SET 2": "code-switch token" in joined,
    }
    print()
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"  {'✅' if ok else '⛔'} bad-sample asserts: {name}")

    good = scan_prompt_text(_GOOD_SAMPLE, language="BM", pace="BRISK_UGC")
    print(f"\n[GOOD SAMPLE] expected CLEAN — {len(good)} finding(s):")
    for f in good:
        print(f"  ❌ {f}")

    print(f"\n{'─' * 70}")
    if failed:
        print(f"⛔ SELF-TEST FAILED — bad sample missed: {', '.join(failed)}")
        return 1
    if good:
        print("⛔ SELF-TEST FAILED — good sample produced findings (false positive).")
        return 1
    print("✅ SELF-TEST PASSED — leaked output blocked on all defect classes; "
          "clean output passes.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", help="Path to a raw prompt text file.")
    parser.add_argument("--language", default="BM")
    parser.add_argument("--pace", default="BRISK_UGC")
    args = parser.parse_args()

    if not args.prompt:
        return _self_test()

    path = Path(args.prompt)
    if not path.exists():
        print(f"⛔ File not found: {path}")
        return 1

    findings = scan_prompt_text(
        path.read_text(encoding="utf-8"), language=args.language, pace=args.pace
    )
    if findings:
        print(f"⛔ BLOCKED — {len(findings)} finding(s):")
        for f in findings:
            print(f"  ❌ {f}")
        return 1
    print("✅ CLEAN — no prompt-quality defects detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
