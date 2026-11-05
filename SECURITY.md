# Security and Contact Policy

Edition label: `2026-11`

## Security contact

- Email: `security@disclosureworks.ai`
- Corrections and removal requests go to `corrections@disclosureworks.ai`; see [Corrections and Removal](corrections-removal.md).

This site and its public source repository, [`github.com/DisclosureWorks/parallax-atlas`](https://github.com/DisclosureWorks/parallax-atlas), carry only the public DisclosureWorks Sourcebook contract and approved monthly edition data.

### Report:

Report these by email to the addresses above.

- schema regressions
- broken manifests
- broken provenance links
- security or privacy concerns

## Where to send reports

Send corrections, removal requests and feedback to `corrections@disclosureworks.ai`, and security
and privacy reports to `security@disclosureworks.ai`. We don't take reports through GitHub.

**Never post a victim's identity, a minor's identity, or anyone's private information in a
public issue, pull request or comment.** Anything posted there is public at once and can be
copied before it is taken down. Email it instead.

## Incident response

*Applies to DisclosureWorks Publications and the DisclosureWorks Sourcebook.*

### 1. What counts as an incident

A publication incident is any case where material reaches a public surface that should not
have. Specifically:

- Restricted, sealed, or embargoed content published.
- A victim or minor identified, in breach of [the redaction policy](https://publications.disclosureworks.ai/privacy/) § 2.
- Personal data of a victim or minor published, or medical information about a private
  individual who is not a subject of the record.
- A credential or secret published.
- Unreviewed content published — an item that never cleared
  [legal and privacy review](https://publications.disclosureworks.ai/methods/).
- Recovered-redaction content published, in breach of [the redaction policy](https://publications.disclosureworks.ai/privacy/) § 4.
- An item published to the wrong destination repository.
- Internal paths, private source files, or application code appearing in a public build.

A *security* vulnerability in the hosting surface is reported to the security contact above and
handled alongside this policy; it becomes a publication incident only if it exposed content.

### 2. Severity

| Severity | Definition | Response |
|---|---|---|
| **SEV-1** | A victim or minor is identified, or personal data of a victim or minor is exposed | Immediate suppression, before diagnosis |
| **SEV-2** | Restricted, sealed, or unreviewed content is public; a secret is exposed | Suppress the same day |
| **SEV-3** | Wrong-destination publication, internal path leakage, or a build-hygiene failure with no sensitive content exposed | Fix in the next patch release |

At SEV-1, suppression comes before understanding. Do not hold a fix while establishing how
it happened.

### 3. Response sequence

1. **Suppress.** Take the affected material off the public surface using the rollback and
   cache-invalidation runbooks for these public surfaces. Rollback is per-repository and each
   was tested independently.
2. **Preserve.** Before changing anything else, capture what was published, the edition and
   patch, the build inputs, the registry state, and the gate output that let it through.
   This is the evidence for the post-mortem and it is destroyed by a hasty rebuild.
3. **Scope.** Determine what was exposed, for how long, and to whom it plausibly propagated
   — mirrors, archive snapshots, agent ingests, feed consumers.
4. **Notify.** Per § 4.
5. **Remediate.** Publish the corrected patch release with a notice
   ([the corrections policy](corrections-removal.md#corrections-policy) § 5). For SEV-1 the notice records the category, never
   the material or the person.
6. **Post-mortem.** Per § 5.

### 4. Notification

- **The publication owner**, immediately, at any severity.
- **An identified affected individual**, at SEV-1, where we can reach them and where contact
  would not itself cause harm or re-identify them to someone else. This judgement is the
  owner's.
- **Publicly**, at SEV-1 and SEV-2, through the correction notice and the removals log —
  recording that an incident occurred, its category, and its duration, without restating the
  material.
- **Known downstream mirrors**, at SEV-1, on a best-effort basis. See § 6.

We do not stay silent about a SEV-1 or SEV-2 because disclosure is embarrassing. A publisher
whose incidents are invisible has an archive nobody can calibrate their trust in.

### 5. Post-mortem — the part that actually prevents recurrence

Every SEV-1 and SEV-2 gets a written post-mortem, and it is not closed until all four of
these exist:

1. **What happened**, on a timeline, without attributing blame to an individual.
2. **Which control should have caught it** — and specifically whether the gate lacked the
   check, had the check and failed, or was bypassed.
3. **A regression test that reproduces the failure**, added to our pre-publication test suite.
   The established pattern is that a fixture that is not blocked fails the build. An incident that does not become a fixture is an incident we have
   licensed to happen twice.
4. **The fix**, landed and verified against that fixture.

The post-mortem is published in summary form for SEV-1 and SEV-2.

### 6. The limit, stated plainly

Containment is not erasure. Under CC BY 4.0, with a DisclosureWorks Sourcebook designed for automated ingest,
material that was public for any period may have been copied. We can suppress, correct, and
notify. **We cannot guarantee retraction**, and we will not tell an affected person that we
can.

This is the same limit recorded in [the removals policy](corrections-removal.md#removals-policy) § 6, and it has the same
consequence: the fail-closed pre-publication gates are the real control. Incident response
is what happens after they have already failed.
