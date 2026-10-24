# CrystalLens for Personal Privacy

This fork is becoming a tool for auditing **your own online exposure**: find
information you want to remove, understand the evidence, and take action.

The upstream application screens employees and candidates. Replacing that workflow
requires more than changing its labels or AI persona. This branch adds the first
independent privacy workflow: a local, deterministic audit of a post export.

**Current scope:** the CLI below is offline and uses only Python's standard library.
The legacy Flask web app still contains screening prompts, shared reports, Apify
scraping, and Gemini integration. It has not been converted or integrated with the
new audit engine. See the [rework plan](docs/personal-privacy-rework.md) for findings
and the ordered migration, and [historical setup](docs/legacy-web-app.md) for the old
app. `python run.py` starts that legacy app, not the new audit workflow.

## Run an offline audit

From the repository root, with Python 3.9 or newer:

```bash
# No pip install, database, .env, API credentials, or model required.
python -m crystallens_privacy examples/posts.example.json

# Keep your imports and reports in the ignored directories.
mkdir -m 700 -p privacy-data privacy-reports
python -m crystallens_privacy privacy-data/posts.json \
  --output privacy-reports/audit.json
```

By default the report contains categories, priorities, suggested actions, and exact
source spans, **without copying matched values, post text, URLs, or author metadata**.
It still contains sensitive metadata about potential exposures; treat it as private.
`--output` creates a new file with POSIX mode `0600` and refuses to overwrite existing
files or symlinks. Parent-directory and non-POSIX access controls remain your responsibility.
The CLI creates no database, cache, or log of the input. Your source export remains
on disk; deleting a report does not delete the source or any backups.

To include matched values and source URLs deliberately:

```bash
python -m crystallens_privacy privacy-data/posts.json \
  --include-evidence --output privacy-reports/audit-with-evidence.json
```

That report can contain credentials and personal information. Stdout is also an
explicit report destination; shell redirection does not inherit `--output`'s file
creation protections. No values are revealed by default, even on stdout.

## Input and evidence references

Input is a UTF-8 JSON **list**, with a string `text` in each object. An optional
string `url` is copied only with `--include-evidence`. Other fields are ignored.
Native platform archives must be normalized first; archive adapters are future work.
You can pipe the same JSON format using `-` as the input path.

```json
[
  {"text": "Contact example@example.com", "url": "https://example.com/posts/1"}
]
```

`post_index` is the one-based position in this list. Each finding's `span` uses
zero-based Python string offsets: `posts[post_index - 1]["text"][start:end]` recovers
the evidence, including when text contains emoji. Keep the input order and text
unchanged when resolving references. These references are local provenance, not
proof that something was publicly visible or authored by you.

Inputs larger than 16 MiB or 10,000 posts are rejected rather than silently truncated.
All accepted post text is scanned. Stable finding IDs within an unchanged input
allow reports to be compared without storing raw values in IDs.

## What it detects

| Candidate exposure | Suggested priority | Action |
| --- | --- | --- |
| Private-key headers or labeled credentials | High | Verify and rotate/revoke before removing |
| US SSN-shaped text | High | Verify and remove if sensitive |
| Email addresses or North American phone patterns | Medium | Review whether contact information should be public |

Every finding starts as `needs_review`. Pattern matches can be fictional, quoted,
intentional, or someone else's information. Priorities describe information
exposure, not a person's trustworthiness. There is no aggregate person score and
no political, religious, character, or employment-suitability assessment.

This initial detector is narrow. It misses many secrets, international contact
formats, addresses, images, location patterns, and contextual concerns. Empty
findings do not establish that your account is safe. Nothing is automatically
deleted or submitted to a platform.

## Validation

```bash
python -m unittest discover -s tests -v
```

The tests cover default evidence minimization, exact Unicode references, malformed
and oversized imports, private output creation, overwrite/symlink refusal, and a
CLI run with third-party Python packages disabled.

## Attribution and licensing

Forked from [SecFathy/CrystalLens](https://github.com/SecFathy/CrystalLens).
The inherited README claimed MIT licensing, but this repository contains no
LICENSE file. Resolve the upstream license grant before representing the entire
project as MIT licensed or redistributing it under that assumption.
