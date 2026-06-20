# Project Overview

Bosmax Command Centre is the repository-governed control layer for a retained BOSMAX Custom GPT package. The objective is to keep the retained files versioned, auditable, and releasable without treating loose uploads as the operating source of truth.

## System Layers

- GitHub repository: authoritative version-control and release-governance layer.
- `Bosmax-Command-Centre/knowledge-pack/`: retained production assets under canonical filenames.
- Validator scripts: deterministic parse/open/hash checks for retained assets.
- Custom GPT: runtime assistant layer that consumes the reviewed package.
- Notion: downstream operator interface and database surface.

## Governance Model

- Branch plus PR is mandatory for every change.
- Validation proof is mandatory before merge.
- Content edits to business assets are not implied by packaging work.
- Syntax-only maintenance patches must be documented precisely and reviewed.
