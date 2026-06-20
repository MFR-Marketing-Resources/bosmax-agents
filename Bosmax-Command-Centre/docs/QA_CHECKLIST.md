# QA Checklist

## Pre-Commit

- Confirm all retained files are present under canonical paths.
- Confirm no business-copy rewrite occurred.
- Run `.\Bosmax-Command-Centre\scripts\validate_bosmax_pack.ps1`.
- Review JSON, YAML, CSV, and XLSX validation output.
- Review manifest SHA256 comparisons.
- Review the retained-package count note.
- Confirm macro execution remains marked `NOT VERIFIED` unless actually executed.
- Review `git status --short` and `git diff --stat`.

## Pre-Release

- Confirm PR body includes validation proof and known gaps.
- Confirm any YAML repair is syntax-only and line-specific.
- Confirm no direct push to `master`.
- Confirm merge approval is complete.
- Confirm only reviewed retained-package assets are used for the Custom GPT upload.
