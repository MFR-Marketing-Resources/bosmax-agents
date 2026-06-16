# BOSMAX Notion CSV Append Protocol
## Status: ACTIVE
## Scope: Copywriting Landbank / Poster Row / Operator Import Governance

---

## Purpose

This protocol governs BOSMAX work when the operator wants to add new rows to a
Notion database by CSV import.

Notion CSV import is treated as append-only unless the operator explicitly
authorizes a full reimport. BOSMAX must therefore generate delta rows only and
must verify live database state before assigning any CSV-controlled IDs.

This protocol is governance only. It does not authorize BOSMAX to invent new
landbank rows by itself.

---

## Trigger Phrases

Apply this protocol when the request includes phrases such as:

- tambah row database
- update database
- append landbank
- tambah CSV Notion
- tambah row Notion
- continue Poster ID
- continue Landbank Row ID
- prepare Notion import CSV
- add new rows for import
- append copywriting landbank

If the request intent is ambiguous between prompt generation and database growth,
default to `APPEND_ONLY_DELTA_CSV` and run the database state gate first.

---

## Default Mode

`APPEND_ONLY_DELTA_CSV`

Meaning:

- the agent generates only the new rows requested for the next import batch
- the agent does not regenerate the full database export
- the agent does not assume Notion will sync, merge, deduplicate, or update
  existing rows by key during import

Full database reimport is forbidden unless the operator explicitly asks for a
full replacement export and accepts the duplicate risk.

---

## Notion Database State Gate

Before generating append CSV rows, the agent must inspect current database state
from one of these proof surfaces:

1. live Notion query / API response
2. live browser inspection of the target database
3. operator-supplied fresh export / snapshot from the current session

The gate is incomplete unless all items below are captured:

1. target database title
2. target database URL or database ID
3. import-relevant schema
4. current row count
5. ID property name
6. ID property mode:
   - `NOTION_AUTO_ID`
   - `CSV_CONTROLLED_CUSTOM_ID`
7. latest existing custom ID, if present
8. max numeric suffix, if present
9. latest batch marker or import cohort marker, if present
10. collision scan basis against existing rows

If any item is missing, the append job is blocked.

---

## Blocked Mode

The agent must stop and report `APPEND BLOCKED` when:

- live database state has not been verified
- the database schema is not available
- the ID property type cannot be determined
- the current highest custom ID cannot be proven
- collision risk cannot be ruled out
- the operator requests append behavior but only provides an old row-count note
  such as `100-row landbank`

Required blocker posture:

- do not guess numbering
- do not emit placeholder CSV
- do not emit a full replacement CSV as a workaround
- do not promote repo prose snapshots into current database truth

---

## Snapshot Law

Statements such as `100-row landbank` are last-known snapshots only.

They may be used as historical context, but never as:

- current row count authority
- current high-water mark authority
- ID continuity authority
- duplicate/collision clearance

Live Notion state, or a fresh operator-provided snapshot from the current
session, always outranks old repo prose.

---

## Numbering Law

### Case A — Notion-managed Unique ID / auto-increment

If the target database uses a Notion-managed `Unique ID` or equivalent
auto-increment property:

- do not populate that property in CSV
- let Notion assign it during import
- still perform collision checks on other stable keys if they exist

### Case B — CSV-controlled custom IDs

If the target database uses a custom field such as `Poster ID` or
`Landbank Row ID`:

- treat that field as CSV-controlled
- derive the next numeric range from the verified live high-water mark
- preserve the existing prefix and zero-padding pattern
- ensure the new batch is continuous with no gaps unless the operator explicitly
  requests a reserved gap

Example:

- last live `Poster ID` = `POSTER_0100`
- next append batch of 5 rows = `POSTER_0101` to `POSTER_0105`

The same law applies to `Landbank Row ID` or any equivalent custom field.

---

## Validation Law

Before any CSV is finalized, the agent must validate:

1. CSV parseability
2. required columns present
3. duplicate IDs within the new batch
4. collisions against existing live IDs
5. numeric continuity for custom IDs
6. row-key collision risk on stable business keys, if those keys exist
7. whether any Notion-managed auto ID field has been incorrectly populated

If any validation fails, the batch remains blocked until corrected.

---

## Manifest Requirement

Every append CSV job must produce a manifest. The manifest may be Markdown,
YAML, or JSON, but it must contain these fields:

- target_database_title
- target_database_url_or_id
- proof_timestamp
- proof_source
- row_count_before_append
- id_property_name
- id_property_mode
- last_existing_custom_id
- max_numeric_suffix
- requested_new_row_count
- generated_custom_id_range
- auto_id_columns_left_blank
- collision_scan_result
- csv_output_scope
- qa_checklist_result
- operator_warnings

If the job is blocked, the manifest must still exist and clearly state why no
CSV was generated.

---

## QA Checklist Requirement

Every append job must include a checklist confirming:

- database state verified
- schema verified
- row count verified
- ID mode verified
- high-water mark verified
- delta-only scope confirmed
- auto-ID columns left blank where required
- custom ID continuation verified where required
- duplicate scan passed
- collision scan passed

No checklist, no append approval.

---

## Forbidden Behavior

- generating a full replacement CSV for a simple append request
- assuming Notion CSV import will merge or update existing rows by key
- manually filling Notion-managed `Unique ID` / auto-increment fields
- restarting custom ID numbering from stale repo snapshots
- treating `100-row landbank` as permanent truth
- skipping collision checks
- skipping the manifest
- skipping the QA checklist

---

## Repo Authority Order

For append governance, authority resolves in this order:

1. live current-session database proof
2. this protocol
3. `.claude/BOSMAX_CURRENT_STATE.md`
4. relevant BOSMAX skills
5. historical repo prose and older snapshots

Repo files may define the law, but they do not replace live database state.

---

## Scope Boundary

This protocol changes BOSMAX governance only.

It does not:

- generate creative copy by itself
- approve direct Notion writes
- rewrite BOSMAX prompt architecture
- override product truth in `products/*.yaml`

---

*BOSMAX Notion CSV Append Protocol | v1.0 | 2026-06-16*
