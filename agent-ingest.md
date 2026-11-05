# Agent Ingest Guidance

Visible edition label: `2026-11`

The DisclosureWorks Sourcebook is published in fixed, citable editions at
`https://sourcebook.disclosureworks.ai`. Earlier addresses redirect permanently
(301) to the same path; follow redirects or use the new host. One page is a
DisclosureWorks Sourcebook entry.

Atlas was the Sourcebook's earlier name; it remains in IDs, field names and addresses so that existing links and citations keep working.

**Footnote coverage.** The citation check covers an entry's main text only. Headings, the lists of related entries and sources, and open questions may state facts without a footnote. Do not treat those parts as cited; use the footnoted text or the source.

`llms.txt` is the entry point for agents. It links the movable latest-edition index,
the immutable edition manifest, the three JSON Lines (JSONL) feeds, and their schemas.
An agent should select one immutable edition and keep every request within that root.

## Package files

- `objects.jsonl` has one record per published page, including the output checksum,
  exact approved-source checksum, topics, provenance, rights, and approval time.
- `links.jsonl` records page and citation edges with their source line. A page edge
  outside the edition is retained with `unresolved: true`.
- `chunks.jsonl` splits each page at Markdown headings and provides stable ordinal
  chunk identifiers, heading paths, character offsets, text, and checksums.
- `SHA256SUMS` verifies the edition payload. `manifest.json`, `SHA256SUMS`, and the
  archive are bound directly by manifest package hashes and are omitted from the
  checksum list to avoid recursive self-hashing.
- The edition archive is a deterministic, portable copy of the edition payload.
  Its archived manifest uses an all-zero archive checksum as the self-reference
  placeholder; the adjacent live manifest carries the archive's actual checksum.

The root-level `objects.schema.json`, `links.schema.json`, and `chunks.schema.json`
files are JSON Schema draft 2020-12 schemas for individual JSONL records.

## Example records

Object:

```json
{"reference_status":null,"assessment":null,"approved_at":"2026-10-26T18:00:00Z","banner":null,"path":"editions/2026-11/atlas-example.md","provenance":"approval record","public_id":"atlas-example","rights":"CC BY 4.0","sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","source_content_hash":"abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789","title":"Example","topics":["oversight"],"url":"/editions/2026-11/atlas-example/"}
```

Link:

```json
{"anchor_text":"Source report","from":"atlas-example","kind":"citation","position":18,"to":"source-report"}
```

Chunk:

```json
{"char_end":112,"char_start":31,"chunk_id":"atlas-example-0002","heading_path":["Example","Findings"],"public_id":"atlas-example","sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","text":"## Findings\n\nPublic finding.\n"}
```

## Verification

From the edition directory, run `sha256sum -c SHA256SUMS`. Verify the remaining
control files using `package.checksums.sha256` and `package.archive.sha256` in
`manifest.json`. To inspect the archive without extracting it, run
`tar -tzf atlas-<edition>.tar.gz`; entries are sorted under the edition directory,
with modification time and numeric owner/group set to zero.

Manifest formats 2 and 3 bind the signed cutoff fingerprint and record identifier, Git
head, semantic component versions, exclusion reasons, per-page approval times,
exact-source hashes, and every package artifact. The legacy `approvals_hash` remains
alongside `approvals.hash` for format-1 consumers.

Allowed inputs are approved Sourcebook edition files, public manifests, and public
schemas. Private wiki state, application state, unpublished worktrees, and the
Publications repository tree are not package inputs.


## Assessment contract (manifest format 3)

Format 3 adds `reference_status` and `assessment` to each manifest `pages` entry
and each `objects.jsonl` record. The same fields travel in candidate records.
Consumers must support format 3 explicitly; existing field names and identifiers
keep their names. Older immutable editions retain their published formats.

`reference_status` is `reference`, `assessed`, or null for legacy pages that have
not opted in. `assessment` is null for legacy and Reference pages. For Assessed
pages it is an object with these exact keys:

| Key | Value |
|---|---|
| `conclusion` | Non-empty central conclusion text |
| `wep` | Exact unbracketed label from the evidence-assessment schema |
| `confidence` | `high`, `medium`, or `low` |
| `source_tier` | `primary-multiple`, `primary-single`, `secondary`, `journalistic`, or `speculative` |
| `corroboration` | `independent`, `partial`, `single-source`, or `contradicted` |
| `basis` | Non-empty list of `[[sources/source-slug]]` references to source pages |
| `would_revise` | List of checkable conditions; non-empty at LIKELY or higher |
| `counterargument` | Text; non-empty at LIKELY or higher |
| `response` | Text; non-empty at LIKELY or higher |
| `assessed` | Valid calendar date, serialized as `YYYY-MM-DD` |
| `change_record` | Repository-relative change-record reference, or empty before a change |

Optional lower-grade revision fields normalize to an empty list or empty text.
Basis references identify the source pages; they are not permission to access
private originals. Public citation edges remain in `links.jsonl` when resolvable.
Read [How we grade conclusions](/grading/) for labels, probability bands, confidence,
and revision policy. A null status is legacy metadata, never an assessment-pending
state. The exporter refuses pending or invalid assessments before build.

All source frontmatter bytes enter the source hash and page fingerprint. Status
and assessment prose also enter the rendered page checksum, while structured
fields enter manifest and package checksums. Editing a grade requires fresh
exact-source approval and invalidates the cached page.

For a format-2 edition, absent `reference_status` and `assessment` normalize to
null. Format 3 requires both fields even for pages without a grade. The root
object schema accepts legacy records; use the manifest format and compare each
complete object projection to `pages[]` to detect fields dropped from format 3.
Unknown manifest versions are unsupported, not implicitly forward-compatible.
