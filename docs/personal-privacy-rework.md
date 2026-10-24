# Reworking CrystalLens into a personal privacy tool

## Product contract

Help a person answer: **What have I exposed, where is the evidence, and what can I
do about it?** Start with one person's local export. Preserve their control over
imports, analysis, disclosure, and deletion. Detection is an aid to their review;
it is not a judgement of their character or a guarantee of safety.

The target loop is: import → identify candidate exposures → inspect evidence →
dismiss or confirm → choose an action → verify the result. For contextual material,
let the owner define what concerns them and mark material for review. Avoid
automatically treating identity, beliefs, health, sexuality, or political speech
as negative indicators.

## Findings in the current fork

Reviewed against main commit `e9356113da97a99897fd256c2d2d10d7e50a6cb0`.
Paths below refer to that baseline unless stated otherwise.

| Area | Evidence in the code | Rework |
| --- | --- | --- |
| Screening remains the core output | `app/services/ollama_service.py` has single, staged, fallback, and repair prompts with political/religious orientation and suitability dimensions; `gemini_service.py` has its own prompt and result mapping | Replace the contract with typed exposure findings; share one schema across providers and all retry paths |
| Scores manufacture certainty | `app/analysis/routes.py:start_analysis` fabricates a score when missing, including after provider failure; Ollama's unstructured parser assigns 50 | Store incomplete/error states explicitly; no person-level scores and no successful audit on a parse failure |
| Local inference does not mean local collection | `apify_service.py` submits account handles/URLs to actors, obtains datasets, and copies raw actor output into each processed post | Imports first; third-party collection is a separate, explicit opt-in with a data preview |
| Cloud inference sends post content and employment metadata | `gemini_service.py:_build_single_prompt` constructs a full prompt and `_generate_response` sends it externally | Keep cloud providers disabled unless enabled deliberately; show destination and exact payload before each disclosed batch |
| Roles do not isolate personal data | `Employee` has no owner FK; employee, job, report, dashboard, and CSV routes query shared data | Prefer single-user local operation first. Before multi-user use, introduce ownership and enforce it on every query, export, mutation, and job |
| Retention is indefinite | `ScrapingJob.scraped_data` retains posts and nested `raw_data`; `AppSetting` stores API keys in plaintext; `AuditLog.details` includes names/handles, including deletion logs | Minimize fields, set retention policy, separate secrets, and make purge cover derived records and identifying log data |
| Citation provenance is fragile | Prompt builders slice to 50/60 posts while routes pass/count all posts; report links reconstruct indexes from job contents | Freeze the analyzed input set and IDs; count only supplied records; validate quotes and references against that set |
| Untrusted content reaches rendering | `analysis/view.html` constructs anchor markup from source URLs via `innerHTML`; PDF export passes model strings to ReportLab `Paragraph` markup | Use safe DOM/text construction, allow only HTTP(S) links, and escape PDF markup. Validate provider output before rendering |
| Deployment can expose the exposure database | `config.py` has a predictable fallback session secret and development debug configuration; original `run.py` binds all interfaces; templates load CDN assets | Require a persistent generated secret, use loopback/no debugger by default, bundle static assets, and harden sessions before network hosting |

Draft [PR #1](https://github.com/jamesbiederbeck/CrystalLens/pull/1) already proposes
privacy wording and new prompt dimensions. Use it as a source of copy, not as proof
that the data boundaries are fixed. Avoid simply merging it and calling the
conversion complete. Old database prompt overrides also need a deliberate reset
or migration when the new schema replaces the screening prompts.

## First implementation in this PR

`crystallens_privacy` is a separate, standard-library-only engine and CLI. It does
not import `app`, initialize the database, read `.env`, call providers, fetch URLs,
or execute instructions in post content. This avoids sending a self-audit through
the existing surveillance pipeline while the web app is reworked.

It accepts normalized posts, checks every accepted text record against a small
set of deterministic patterns, and returns per-match source references, category,
priority, review status, and suggested action. It excludes raw evidence and source
metadata from reports by default. Evidence disclosure is a named CLI option.
Output files are created exclusively with owner-only POSIX permissions. Imports
are bounded and malformed input errors do not echo the source payload.

This PR also changes the legacy dev server to loopback with its interactive
debugger disabled, and ignores the documented local import/report directories.
It does not integrate the new engine into the legacy web app or migrate its data.

## Ordered migration and acceptance criteria

### 1. Complete the local exposure workflow

Build explicit adapters for selected platform exports and reuse this detector
library. Preserve platform post IDs, source time, capture/import time, authorship
and visibility claims with their source, and record adapter/version information.
Distinguish originals, reposts, replies, and third-party mentions. Do not infer
that owning an archive means every record was written by its owner.

Add review state (`confirmed`, `dismissed`, `action_planned`, `resolved`) and a
local review UI. Findings need source IDs and spans, detector version, owner notes,
and actionable reasons. Keep exact evidence separately from minimized reports.
Define stable cross-import IDs and explicit handling of edited/deleted posts;
the current list-position IDs are only stable within an unchanged input.

**Acceptance:** fixtures for each supported export; missing or unsupported fields
produce visible coverage gaps; a finding resolves to the exact original record;
review decisions survive reimport without silently conflating unrelated posts.

### 2. Make the web app respect the same boundaries

Replace Employee/HR fields and screening dashboards with an owner-controlled
workspace and findings. Reuse the local finding schema instead of stuffing new
meanings into `character_assessment` and `behavioral_insights`. Introduce versioned
migrations; `db.create_all()` does not migrate existing tables.

Enforce ownership server-side if adding multiple users. Decide how legacy profiles
are assigned before exposing them; do not automatically grant all users access.
Test guessed IDs, dashboards, exports, job polling, deletion, and background tasks.
Return explicit failed/partial states; never backfill a privacy score from flag
counts. Remove the remaining screening prompts and stored overrides.

**Acceptance:** user A cannot read/export/mutate user B's records; errors never look
like successful audits; web and CLI findings agree on the same normalized input.

### 3. Bound storage and outbound data

Keep cloud scrapers and providers behind a server-enforced off-by-default policy,
not just hidden buttons or the presence of an API key. A chosen local Ollama
endpoint can itself be remote: show the configured endpoint and what is sent.
Tests/status checks, retries, and background jobs must honor the same policy.
Import/review pages should work with outbound traffic blocked and no CDN calls.

Minimize stored fields and logs, move credentials out of general settings, define
retention, and provide workspace purge that covers imports, findings, derived
reports, jobs, and identifying audit details. Document backups and remote copies
as separately managed; local deletion cannot guarantee their erasure. Do not
promise secure erasure on SSDs or ordinary database deletion.

**Acceptance:** a network-denied local workflow succeeds; cloud-disabled paths
make no requests; purge tests cover derived data and logs; restored backups have
a documented retention/deletion strategy. Require a non-default secret and safe
rendering before broader hosting.

### 4. Add optional contextual AI after evidence is reliable

Use local models for bounded suggestions about location routines, household
information, and owner-defined contextual concerns. Treat post text as untrusted
data, never operational instructions. Models should receive no tools or platform
credentials. Delimit data, validate a strict findings schema, require source IDs
and exact quotes, reject unsupported references, and mark inference separately
from deterministic evidence. A prompt instruction alone does not prevent injection.

Keep "no evidence found", "not analyzed", "parse failure", and "model uncertain"
distinct. Build an evaluation set with genuine exposures, intentional public
contacts, quotes, satire, and hostile prompt text; track false positives, missed
exposures, citation validity, and analyzed coverage. Cloud analysis additionally
needs explicit payload disclosure and user choice.

**Acceptance:** unsupported citations cannot become confirmed findings; an invalid
response stays failed/partial; configured context limits never silently drop posts;
the tool works without AI; user text cannot request network calls or deletion.

### 5. Close the remediation loop

Begin with links and instructions for editing visibility, removing a post,
requesting a takedown, or rotating credentials. Never assume deletion fixes a
published credential: revocation comes first. Later add narrowly scoped platform
actions with a preview and explicit confirmation of each selected action.

**Acceptance:** every confirmed finding has an actionable next step; "resolved"
records what was verified and when, without claiming that all cached copies are
gone. Monitoring is opt-in and owner-scoped, with explicit retention.

## Limits of the first slice

Regex is not a full PII detector. Matches do not prove authorship, exposure,
credential validity, or harm. This release covers text only and supports a
normalized import format rather than native archives. It has no persistent review
state, image/EXIF analysis, encrypted workspace, browser UI, or automated cleanup.
Local filesystem permissions do not protect against a compromised host or its
administrator. The legacy web app retains the issues listed above except for its
development bind/debug defaults. Resolve the repository's missing license grant
before publishing a licensed distribution.
