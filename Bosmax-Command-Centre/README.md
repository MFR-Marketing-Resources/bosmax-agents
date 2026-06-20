# Bosmax Command Centre

Repo: `MFR-Marketing-Resources/bosmax-agents`

Bosmax Command Centre is the GitHub source-of-truth control layer for the BOSMAX Custom GPT retained knowledge pack. This subtree is the audit, version-control, QA, and release-governance surface for the retained package without rewriting approved business content.

## Runtime Distinction

- GitHub: master source, version control, audit trail, QA gate, release governance.
- Custom GPT: runtime assistant and operator-facing execution interface.
- Notion: operator database and UI layer.
- Codex: audit, repair, validation, and PR-proof engine.

## File Structure

```text
Bosmax-Command-Centre/
  README.md
  AGENTS.md
  SKILLS.md
  CHANGELOG.md
  docs/
  knowledge-pack/
  scripts/
```

## Knowledge-Pack Boundary

The `knowledge-pack/` directory stores retained production assets only. Those files are imported under canonical filenames and should not be casually edited. Any required content repair must be separately scoped, validated, and reviewed through branch and PR.

## Validate

From the repo root:

```powershell
.\Bosmax-Command-Centre\scripts\validate_bosmax_pack.ps1
```

The validator prints file sizes, SHA256 values, JSON/YAML/CSV parse results, XLSX sheet names, manifest hash comparisons, the retained-package count discrepancy, and the macro-execution status.

## Release To Custom GPT

1. Branch from `master`.
2. Update only the reviewed `Bosmax-Command-Centre/` surfaces.
3. Run the validator and review the hash/parse output.
4. Commit and open a PR with proof.
5. Merge after review.
6. Upload only the reviewed retained-package files from `knowledge-pack/` to the Custom GPT release bundle.

## Current Retained Package Status

- Current retained intake resolves to 10 canonical files.
- `BOSMAX_FINAL_11_FILE_MANIFEST.csv` still uses an `11` filename label.
- The manifest content currently lists 10 rows, including the manifest itself as `SELF_REFERENCE_NOT_HASHED`.
- If `VIDEO_PROMPT_COMPILER_TEMPLATES.yaml` receives a syntax-only YAML quoting fix, the manifest hash for that file must be treated as drift until an operator decides whether to refresh the manifest later.

## Warning

Do not casually edit copywriting, hooks, dialogue, CTA text, product truth, avatar descriptions, workbook contents, or commercial claims from this subtree. Use a scoped branch, validator proof, and PR review for every change.
