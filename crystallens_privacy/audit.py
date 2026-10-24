"""Conservative text detectors. Matches are review candidates, not verdicts."""

import re


# Rule priority describes the exposed information, never the person posting it.
RULES = (
    (
        "private_key", "high",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
        "If a real key was published, revoke or replace it first, then remove the post.",
    ),
    (
        "credential", "high",
        re.compile(
            r"\b(?:password|api[_ -]?key|access[_ -]?token|secret)"
            r"\s*[:=]\s*[\"']?([^\s\"'<>]{8,})", re.IGNORECASE
        ),
        "Check whether this is a real credential. Rotate it before editing or deleting the post.",
    ),
    (
        "us_ssn", "high",
        re.compile(r"(?<!\w)(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}(?!\w)"),
        "Review this possible US Social Security number and remove it if sensitive.",
    ),
    (
        "email", "medium",
        re.compile(r"(?<![\w.+-])[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
                   r"(?:[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?\.)+[A-Z]{2,}(?![\w-])",
                   re.IGNORECASE),
        "Decide whether this address should be public; remove or replace it if unwanted.",
    ),
    (
        "north_american_phone", "medium",
        re.compile(r"(?<!\w)(?:\+?1[ .-]?)?(?:\([2-9]\d{2}\)|[2-9]\d{2})"
                   r"[ .-]?[2-9]\d{2}[ .-]?\d{4}(?!\w)"),
        "Review this possible phone number; remove it or use a public contact number.",
    ),
)


def validate_posts(data):
    """Accept only a normalized JSON list. Never guess an archive's structure."""
    if not isinstance(data, list):
        raise ValueError("Input must be a JSON list of post objects.")
    if len(data) > 10000:
        raise ValueError("Input exceeds the 10000-post limit; split it into batches.")
    for index, post in enumerate(data, 1):
        if not isinstance(post, dict) or not isinstance(post.get("text"), str):
            raise ValueError(f"Post {index} must be an object with a string text field.")
        # URL is retained only when evidence disclosure is explicitly requested.
        if "url" in post and not isinstance(post["url"], str):
            raise ValueError(f"Post {index} has a non-string url field.")
    return data


def audit_posts(posts, *, include_evidence=False):
    """Return findings with exact, zero-based Python string spans in source text.

    Raw text and source metadata are excluded by default. A post reference is its
    one-based position in the input, so duplicate IDs and missing URLs are safe.
    """
    posts = validate_posts(posts)
    findings = []
    for index, post in enumerate(posts, 1):
        for category, priority, pattern, action in RULES:
            for match in pattern.finditer(post["text"]):
                finding = {
                    "id": f"post-{index}:{category}:{match.start()}:{match.end()}",
                    "post_index": index,
                    "category": category,
                    "priority": priority,
                    "status": "needs_review",
                    "basis": "pattern_match",
                    "span": {"start": match.start(), "end": match.end()},
                    "evidence": match.group() if include_evidence else "[redacted]",
                    "suggested_action": action,
                }
                if include_evidence and "url" in post:
                    finding["source_url"] = post["url"]
                findings.append(finding)
    return {
        "schema_version": 1,
        "posts_scanned": len(posts),
        "evidence_included": include_evidence,
        "coverage": [rule[0] for rule in RULES],
        "limitations": (
            "Text patterns only; false positives and missed exposures are expected. "
            "This does not verify authorship or public visibility, inspect images, "
            "detect all PII or secrets, or establish that an account is safe. "
            "Locations, routines, contextual reputation concerns, and international "
            "phone formats need separate review."
        ),
        "findings": findings,
    }
