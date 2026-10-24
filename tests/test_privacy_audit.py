import contextlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from crystallens_privacy.__main__ import MAX_INPUT_BYTES, main, read_posts, write_report
from crystallens_privacy.audit import audit_posts


class PrivacyAuditTests(unittest.TestCase):
    def test_findings_resolve_to_original_unicode_text(self):
        text = "🍄 Contact example@example.com; phone (202) 555-0100; api_key=EXAMPLE_NOT_REAL"
        report = audit_posts([{"text": text}], include_evidence=True)
        self.assertEqual({f["category"] for f in report["findings"]},
                         {"email", "north_american_phone", "credential"})
        for finding in report["findings"]:
            span = finding["span"]
            self.assertEqual(text[span["start"]:span["end"]], finding["evidence"])
            self.assertEqual(finding["post_index"], 1)

    def test_default_report_does_not_copy_sensitive_text_or_metadata(self):
        post = {
            "text": "password=SECRET_VALUE_123 and private@example.org",
            "url": "https://example.org/?token=PRIVATE_URL_TOKEN",
            "author": "PRIVATE_AUTHOR",
            "raw_data": {"address": "PRIVATE_ADDRESS"},
        }
        report = audit_posts([post])
        serialized = json.dumps(report)
        for secret in ("SECRET_VALUE_123", "private@example.org", "PRIVATE_URL_TOKEN",
                       "PRIVATE_AUTHOR", "PRIVATE_ADDRESS"):
            self.assertNotIn(secret, serialized)
        self.assertTrue(report["findings"])
        self.assertTrue(all(f["evidence"] == "[redacted]" for f in report["findings"]))
        self.assertNotIn("risk_score", report)

    def test_duplicate_source_ids_still_have_distinct_references(self):
        posts = [{"post_id": "same", "text": "a@example.org"}] * 2
        findings = audit_posts(posts)["findings"]
        self.assertEqual([f["post_index"] for f in findings], [1, 2])
        self.assertNotEqual(findings[0]["id"], findings[1]["id"])

    def test_no_findings_is_not_a_safety_assessment(self):
        report = audit_posts([{"text": "I leave home every day at 9am."}])
        self.assertEqual(report["findings"], [])
        self.assertIn("routines", report["limitations"])
        self.assertNotIn("confidence_score", report)

    def test_private_key_and_ssn_rules_and_obvious_ssn_exclusions(self):
        report = audit_posts([{"text": "-----BEGIN OPENSSH PRIVATE KEY----- 123-45-6789"}])
        self.assertEqual({f["category"] for f in report["findings"]}, {"private_key", "us_ssn"})
        excluded = audit_posts([{"text": "000-12-3456 666-12-3456 999-12-3456 123-00-4567 123-45-0000"}])
        self.assertNotIn("us_ssn", [f["category"] for f in excluded["findings"]])

    def test_invalid_input_fails_without_echoing_source(self):
        for data in ({"posts": []}, [None], [{"text": 1}], [{"text": "", "url": 3}]):
            with self.assertRaises(ValueError):
                audit_posts(data)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for content in (b'{"PRIVATE_CONTENT":', b'\xffPRIVATE_CONTENT'):
                path.write_bytes(content)
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as exc:
                    main([str(path)])
                self.assertEqual(exc.exception.code, 2)
                self.assertNotIn("PRIVATE_CONTENT", stderr.getvalue())

    def test_limits_fail_before_a_report_is_created(self):
        with self.assertRaises(ValueError):
            audit_posts([{"text": ""}] * 10001)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.json"
            with path.open("wb") as stream:
                stream.truncate(MAX_INPUT_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "16 MiB"):
                read_posts(str(path))

    @unittest.skipUnless(os.name == "posix", "POSIX file permissions and symlinks")
    def test_report_is_private_and_never_overwrites_or_follows_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            previous_umask = os.umask(0)
            try:
                write_report(str(path), {"findings": []})
            finally:
                os.umask(previous_umask)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_report(str(path), {"changed": True})
            self.assertEqual(path.read_bytes(), original)
            link = Path(directory) / "link.json"
            link.symlink_to(path)
            with self.assertRaises(FileExistsError):
                write_report(str(link), {"changed": True})
            dangling = Path(directory) / "dangling.json"
            dangling.symlink_to(Path(directory) / "missing.json")
            with self.assertRaises(FileExistsError):
                write_report(str(dangling), {})
            self.assertFalse((Path(directory) / "missing.json").exists())

    def test_cli_runs_without_site_packages_and_supports_stdin(self):
        result = subprocess.run(
            [sys.executable, "-S", "-m", "crystallens_privacy", "-"],
            input=json.dumps([{"text": "contact@example.org"}]),
            text=True, capture_output=True, check=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        report = json.loads(result.stdout)
        self.assertEqual(len(report["findings"]), 1)
        self.assertNotIn("contact@example.org", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_offline_path_does_not_initialize_web_app_or_open_network(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "posts.json"
            target = Path(directory) / "report.json"
            source.write_text(json.dumps([{"text": "a@example.org"}]))
            with patch("socket.socket", side_effect=AssertionError("Network forbidden")):
                self.assertEqual(main([str(source), "--output", str(target)]), 0)
            self.assertTrue(target.exists())
            self.assertNotIn("app", sys.modules)
            self.assertNotIn("flask", sys.modules)


if __name__ == "__main__":
    unittest.main()
