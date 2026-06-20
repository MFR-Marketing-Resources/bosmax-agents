# Custom GPT Deployment

## Intended Upload Surfaces

Upload only the reviewed retained files from `knowledge-pack/`. The repository documents, validator scripts, and PR proof surfaces remain governance artifacts and are not the runtime package themselves.

## Authority Model

- GitHub is the master source and audit surface.
- Custom GPT is the runtime assistant surface.
- Notion is the operator UI/database surface.

## Post-Upload Smoke Test

- Confirm the correct custom instruction file is loaded.
- Confirm the runtime references the retained canonical filenames.
- Confirm prompt generation does not expose block-plan metadata or debug internals.
- Confirm product truth references resolve correctly.
- Confirm any known manifest drift, such as a syntax-only YAML patch, is understood before production use.
