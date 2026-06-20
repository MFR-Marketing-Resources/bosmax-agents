# Release Process

1. Create or update a feature branch from `master`.
2. Limit edits to the intended `Bosmax-Command-Centre/` scope and approved support files.
3. Run `.\Bosmax-Command-Centre\scripts\validate_bosmax_pack.ps1`.
4. Review `git status --short` and `git diff --stat`.
5. Commit with validation status represented truthfully in the PR.
6. Push the branch.
7. Open a PR for review.
8. Merge only after the review accepts both the file changes and the validation evidence.
9. Build the Custom GPT upload package only from reviewed retained files in `knowledge-pack/`.

Only reviewed release files should be uploaded to Custom GPT.
