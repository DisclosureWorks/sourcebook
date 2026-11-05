# Manifest Formats 2 and 3

Visible edition label: `2026-11`

Each immutable edition has `editions/<edition>/manifest.json`. The root-level
`manifest.schema.json` is its JSON Schema draft 2020-12 contract.

The November edition emits format 3. It adds nullable `reference_status` and
`assessment` fields to every `pages[]` entry and object record; see
[schema](/schema/) for the full assessment projection. The root manifest schema
accepts formats 2 and 3, requiring both new fields for format 3. Older immutable
format-2 editions remain valid and retain their original bytes. Object records
have no independent version: use their edition manifest's format. In format 2,
missing assessment fields mean null; in format 3 both fields must be present.
Unknown manifest formats must be rejected.

Format 2 retains every format-1 field and adds the information needed to reproduce
and audit an agent ingest:

- `source_cutoff` is now `{fingerprint, record_id, git_head}`. Only the public
  fingerprint and signed-record identifier are copied from the cutoff record.
- `component_versions` records semantic versions for the edition assembly tool, the
  wiki exporter, and the release build tool.
- `counts.excluded` and `exclusions[{public_id, reason}]` make gate omissions
  reviewable rather than implicit.
- `approvals` records the compatibility hash, page count, and each page's approval
  time. `approvals_hash` remains unchanged for format-1 readers.
- Every `pages[]` item adds `source_content_hash` and `approved_at`; `sha256` remains
  the checksum of the public output bytes.
- `package` binds `objects.jsonl`, `links.jsonl`, `chunks.jsonl`, `SHA256SUMS`, and
  the deterministic archive by path and SHA-256.

## Format 1 to format 2

| Field | Format 1 | Format 2 |
|---|---|---|
| `format` | `1` | `2` |
| `source_cutoff` | Git commit string | signed fingerprint, record ID, and Git commit |
| Component versions | absent | three semantic versions |
| Exclusions | implicit in counts | count plus public reasons |
| Approvals | `approvals_hash` only | compatibility hash plus per-page records |
| Page source checksum | absent | `source_content_hash` |
| Agent package | absent | five path-and-checksum records |

The correction policy and patch-root fields are unchanged. A later edition never
rewrites an earlier immutable edition root.
