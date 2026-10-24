"""Run with python -m crystallens_privacy. Standard library only; no network."""

import argparse
import json
import os
import sys

from .audit import audit_posts


MAX_INPUT_BYTES = 16 * 1024 * 1024


def read_posts(source):
    if source == "-":
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        with open(source, "rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Input exceeds the 16 MiB limit; split it into batches.")
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, RecursionError):
        # JSONDecodeError/UnicodeDecodeError can include source content.
        raise ValueError("Input must contain valid UTF-8 JSON.") from None


def write_report(path, report):
    """Create an owner-only file; never truncate a file or follow a symlink."""
    payload = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(payload)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit your own normalized post export locally, without AI or cloud services."
    )
    parser.add_argument("input", help="UTF-8 JSON list of posts, or - for stdin")
    parser.add_argument("--output", help="Create a new private JSON report (otherwise stdout)")
    parser.add_argument(
        "--include-evidence", action="store_true",
        help="Include exact matches and source URLs; the report will contain sensitive data",
    )
    args = parser.parse_args(argv)
    try:
        report = audit_posts(read_posts(args.input), include_evidence=args.include_evidence)
        if args.output:
            write_report(args.output, report)
        else:
            print(json.dumps(report, ensure_ascii=True, indent=2))
    except ValueError as exc:
        parser.error(str(exc))
    except OSError:
        parser.error("Could not read input or create output. Check permissions and use a new output path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
