# Corrections and Removal

Edition label: `2026-11`

## Corrections policy

*Applies to DisclosureWorks Publications and the DisclosureWorks Sourcebook.*

### 1. The commitment

We correct errors in public, on the record, and without quietly rewriting what was already
published. A reader who cites an edition must be able to see, later, exactly what changed
in it and why.

### 2. What counts as a correction

- A factual error — a date, figure, name, sequence, or attribution that is wrong.
- A citation error — a source that does not say what we said it says, or does not exist.
- A quotation error — text presented as a quotation that does not match the source.
- A computational error — a count, percentage, or derived statistic that does not
  reproduce.
- A provenance error — a document, Bates number, or hash that does not resolve to what we
  claimed.
- In the DisclosureWorks Sourcebook: a schema violation, a broken stable ID, or a manifest
  checksum that does not match its object.

Changes of interpretation, added context, and revised analysis are **not** corrections. They
are new work and belong in the next edition, clearly dated. Calling a changed opinion a
"correction" devalues the word for the cases that need it.

### 3. How to report one

Write to `corrections@disclosureworks.ai`. Include the edition ID, the page or object ID, what is wrong,
and — if you have it — the source that shows what is right. Anonymous reports are accepted
and handled the same way.

You do not need to be the subject of the material to report an error in it.

### 3a. Feedback that is not a correction

General feedback, such as a comment, a question or a suggestion for future work, also goes to
`corrections@disclosureworks.ai`, with the subject line `Feedback`. We read it, but we do not log it
as a correction, and we do not promise a reply. If you think something we published is wrong,
report it as a correction under § 3, so that it gets a severity and a target.

### 4. Triage

We aim to acknowledge within **a few working days**. Severity sets our target for fixing:

| Severity | Meaning | Target |
|---|---|---|
| **1** | The error misstates a fact about an identifiable person, or a core finding does not survive it | A few days |
| **2** | A supporting fact, figure, citation, or quotation is wrong | A few weeks |
| **3** | Typographic, formatting, link, or presentational | Next release |

A severity-1 report that we cannot resolve within a few days gets an
[interim public notice](corrections/index.md#under-review) saying the claim is under review,
rather than silence while we work.

### 5. How a correction is published

Editions are immutable under this publication policy. We do not edit a published edition in
place. Instead:

1. A **[correction notice](corrections/index.md#correction-notices)** is written: what was
   published, what is correct, what evidence changed our mind, and the date.
2. A **patch release** of the affected edition is published carrying the fix — for example
   `2026-10-patch-1`. The original edition remains reachable at its own URL.
3. The **release-history** page and the `latest` pointer are updated.
4. In the DisclosureWorks Sourcebook, the manifest, object checksums, and any dependent derived
   index are regenerated, and the affected stable IDs are named in the notice.

The correction notice is permanent. It is not removed in later editions, and it is not
rolled up or summarised away once the fix is old.

### 6. What we will not do

- Silently amend a published page.
- Withdraw an edition to avoid publishing a notice.
- Correct by deletion where a correction notice is what the record requires.
- Treat a demand to retract accurate, sourced material as a correction request. That is a
  removal request and is handled under [the removals policy](#removals-policy).

### 7. Limits worth stating

Our editions are published under CC BY 4.0 and are designed to be copied, mirrored, and
ingested by research agents. **A correction propagates to our surface, not to
every copy of it.** We can tell you what we got wrong; we cannot reach into a mirror, an
archive snapshot, or a downstream dataset and fix it there. This is a consequence of the
licence we chose deliberately, and it is a reason to get things right the first time rather
than to rely on the correction route.

## Removals policy

*Applies to DisclosureWorks Publications and the DisclosureWorks Sourcebook.*

### 1. Preference order

Where a problem can be fixed without removal, we fix it without removal:

**Correct → redact → restrict → remove.**

A [correction](#corrections-policy) fixes an error. A
[redaction](https://publications.disclosureworks.ai/privacy/) removes specific sensitive content while
leaving the record intact. Removal takes material out of the public edition entirely, and is
the last option because it destroys the citability that the rest of this project exists to
create.

That ordering is a default, not a delay tactic. Where the material is a victim
identification or a minor's identity, we act immediately and sort out the tier afterwards.

### 2. Grounds we act on

We will remove or redact material on any of these grounds:

1. **Identification of a victim or survivor of sexual abuse**, whether by name, image, or
   detail sufficient to identify them — including where the identification is present in the
   underlying public record. That a court file names someone is not a reason for us to
   amplify it.
2. **Identification of a person who was a minor** at the time of the events described.
3. **Material published in error** — anything restricted, sealed, embargoed, or unreviewed
   that reached a public surface. This is also an incident; see [SECURITY.md](SECURITY.md).
4. **Personal data of victims, survivors and minors**, and medical information about
   private individuals who are not subjects of the record.
5. **A court order** requiring removal, or material we learn is under seal.
6. **A credible, specific safety risk** to an identifiable person created or materially
   increased by our publication.

Requests under grounds 1, 2, 4, and 6 are honoured for **private individuals** without
requiring the requester to justify themselves further than establishing that the ground
applies.

### 3. Grounds we do not act on

We will not remove material because:

- It is unflattering, embarrassing, or commercially inconvenient to a public figure acting
  in a public capacity.
- It accurately reports a public record, a court filing, sworn testimony, or an official
  document, and the requester disputes the underlying record rather than our rendering of it.
- The requester asserts an error without identifying one. That is a
  [correction](#corrections-policy) request, and we would rather have it as one.
- A third party objects to material about someone else, absent grounds 1, 2, or 6.

Where we decline, we say so, we say why, and we tell the requester that they may put a
response on the record. We would rather publish a disagreement than quietly bury a request.

### 4. Process

1. **Request** to `corrections@disclosureworks.ai`, identifying the edition, the page or object ID, the
   material, and the ground relied on.
2. **Acknowledgement, which we aim to send within a few working days.** For grounds 1, 2, and 6 we acknowledge and
   act to suppress the specific material immediately, before completing the review.
3. **Review** by the publication owner against § 2 and § 3.
4. **Decision**, in writing, to the requester: granted in full, granted in part, or declined
   with reasons.
5. **Action** — the removal or redaction ships as a patch release of the affected edition,
   per [the corrections policy](#corrections-policy) § 5.
6. **Log entry** in the public [removals log](corrections/removals-log.md).

### 5. The removals log

We publish a running [log of removals](corrections/removals-log.md). Each entry records the
edition, the date, the ground category, and the scope of what was removed. **It does not
record the identity of the subject or the requester**, and it does not restate the removed
material — a log that re-identifies the person it protected would defeat itself.

The log exists so that the removal power is visible and countable. A publisher who can
quietly remove material is a publisher whose archive cannot be trusted; the log is what
makes our removals auditable without exposing the people they protect.

#### 5a. What a reader following a citation finds

The log above is centralised and answers "what has been removed". It does not answer the
question a specific reader has: **they followed a citation to a stable public ID and got
nothing.**

A stable ID that returns nothing is indistinguishable from a publication failure, a bad link,
or a failed site move. A researcher who cited an item in their own work cannot tell whether
we withdrew it or whether publication failed — and the second explanation is the one they
will assume, because it is the more common cause.

**Every removal therefore leaves a marker at the item's own stable ID**, recording that the
item was withdrawn and the date. Nothing else.

- It does **not** record the ground category. The centralised log carries that, aggregated,
  where it cannot be tied back to a specific subject by anyone reading a single URL.
- It does **not** record the subject or requester, for the same reason § 5 gives.

The distinction matters: the log makes the removal power *auditable*, and the marker makes an
individual removal *legible to the person who cited it*. Those are different jobs and one
artifact cannot do both — a per-item marker detailed enough to be auditable would re-identify
the subject, and a log aggregated enough to protect the subject cannot be found by someone
holding a dead link.

### 6. The limit we cannot engineer around — read this before relying on removal

Our editions are published under **CC BY 4.0** and are explicitly designed to be copied,
mirrored, and ingested by automated research agents. The DisclosureWorks Sourcebook exists to
be consumed programmatically.

**Removal from our surface does not retract copies.** We can remove material from the
current edition and every future one. We cannot remove it from a mirror, a web archive, a
downstream dataset, a research agent's index, or anyone's local copy. No
publisher operating under an open licence can, and we will not imply otherwise to make a
removal feel more complete than it is.

What this means practically:

- **Prevention carries the weight, not removal.** The pre-publication gates
  ([https://publications.disclosureworks.ai/methods/](https://publications.disclosureworks.ai/methods/)) are the
  real protection for victims and minors. The removal route is a backstop for what those
  gates miss.
- We will tell a requester honestly what removal achieves and what it does not, at the point
  they ask, rather than after.
- For grounds 1 and 2 we will, on request and where we can identify them, notify known
  downstream mirrors. We cannot compel them.

### 7. Escalation

If a requester disagrees with a decision, they may ask for it to be reconsidered in writing.
**They should know that this goes back to the same person.** The publication owner and the
release approver are the same individual for the 2026-10 edition, so there is no independent
internal appeal. We would rather state that than describe an escalation route that does not
exist.
