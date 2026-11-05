# Schema

Visible edition label: `2026-11`

The Sourcebook public contract is schema-driven.

Required schema surfaces:

- `manifest.schema.json`
- `object.schema.json`
- `provenance.schema.json`

Compatibility is fail-closed: the consumer must reject unsupported schema
versions.


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

The root manifest schema validates formats 2 and 3. Format-2 pages may omit the
assessment projection; consumers normalize absent fields to null. Format-3 pages
must include both fields. Object records use their edition manifest's version;
legacy records may omit both fields, but a format-3 package must not. Audits bind
the complete object projection to its manifest page as well as checking hashes.
