import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = PROJECT_DIR.parent

sys.path.insert(0, str(PROJECT_DIR))

import verify_contribution


class TestContributionVerifier(unittest.TestCase):

    def test_valid_did(self):
        record = {
            "did": (
                "did:key:"
                "z6MksazjmAFoVhiQfbDVEhtFgJ5kKPuDTYS3mGZr5iNZzpzZ"
            )
        }

        passed, detail = verify_contribution.check_did(record)

        self.assertTrue(passed)
        self.assertIn("did:key:", detail)

    def test_invalid_did(self):
        record = {
            "did": (
                "z6MksazjmAFoVhiQfbDVEhtFgJ5kKPuDTYS3mGZr5iNZzpzZ"
            )
        }

        passed, _ = verify_contribution.check_did(record)

        self.assertFalse(passed)

    def test_valid_room(self):
        record = {
            "room": "technocore"
        }

        passed, detail = verify_contribution.check_room(record)

        self.assertTrue(passed)
        self.assertEqual(detail, "room=technocore")

    def test_invalid_room(self):
        record = {
            "room": "lobby"
        }

        passed, _ = verify_contribution.check_room(record)

        self.assertFalse(passed)

    def test_valid_sequence(self):
        record = {
            "seq": 2237678
        }

        passed, detail = verify_contribution.check_seq(record)

        self.assertTrue(passed)
        self.assertEqual(detail, "seq=2237678")

    def test_invalid_sequence(self):
        record = {
            "seq": 0
        }

        passed, _ = verify_contribution.check_seq(record)

        self.assertFalse(passed)

    def test_valid_nonce(self):
        record = {
            "nonce": 1788090521980534600
        }

        passed, detail = verify_contribution.check_nonce(record)

        self.assertTrue(passed)
        self.assertEqual(
            detail,
            "nonce=1788090521980534600"
        )

    def test_invalid_nonce(self):
        record = {
            "nonce": "abc"
        }

        passed, _ = verify_contribution.check_nonce(record)

        self.assertFalse(passed)

    def test_github_url(self):
        record = {
            "artifact_url": (
                "https://github.com/"
                "Jubbic/technocore-did-beginner-guide"
                "/tree/contribution-4"
            )
        }

        passed, detail = verify_contribution.check_artifact_url(
            record
        )

        self.assertTrue(passed)
        self.assertIn("github.com", detail)

    def test_github_url_parser(self):
        owner, repo, branch = (
            verify_contribution.parse_github_url(
                "https://github.com/"
                "Jubbic/technocore-did-beginner-guide"
                "/tree/contribution-4"
            )
        )

        self.assertEqual(
            owner,
            "Jubbic"
        )

        self.assertEqual(
            repo,
            "technocore-did-beginner-guide"
        )

        self.assertEqual(
            branch,
            "contribution-4"
        )

    def test_commit_hash_format(self):
        record = {
            "commit": (
                "7e26b16573e072b6f656eeab1baaa6db94319078"
            )
        }

        passed, detail = verify_contribution.check_commit(
            record
        )

        self.assertTrue(passed)
        self.assertIn(
            "exists locally",
            detail
        )

    def test_proof_matching_record(self):
        record = {
            "did": (
                "did:key:"
                "z6MksazjmAFoVhiQfbDVEhtFgJ5kKPuDTYS3mGZr5iNZzpzZ"
            ),
            "artifact_url": (
                "https://github.com/"
                "Jubbic/technocore-did-beginner-guide"
                "/tree/contribution-4"
            ),
            "commit": (
                "7e26b16573e072b6f656eeab1baaa6db94319078"
            ),
            "proof_file": (
                "fixtures/contribution-4-proof.json"
            )
        }

        record_path = (
            PROJECT_DIR / "sample-contribution.json"
        )

        passed, detail = verify_contribution.check_proof(
            record,
            record_path
        )

        self.assertTrue(passed)
        self.assertIn(
            "Proof verified",
            detail
        )

    @patch("verify_contribution.github_get")
    def test_github_artifact_with_mocked_api(
        self,
        mock_github_get
    ):
        mock_github_get.side_effect = [
            {
                "full_name": (
                    "Jubbic/"
                    "technocore-did-beginner-guide"
                )
            },
            {
                "object": {
                    "sha": (
                        "7e26b16573e072b6f656eeab1baaa6db94319078"
                    )
                }
            }
        ]

        record = {
            "artifact_url": (
                "https://github.com/"
                "Jubbic/technocore-did-beginner-guide"
                "/tree/contribution-4"
            )
        }

        passed, detail = verify_contribution.check_github(
            record
        )

        self.assertTrue(passed)
        self.assertIn(
            "contribution-4",
            detail
        )

    def test_load_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "example.json"

            path.write_text(
                '{"room": "technocore"}',
                encoding="utf-8"
            )

            data = verify_contribution.load_json(path)

            self.assertEqual(
                data["room"],
                "technocore"
            )


if __name__ == "__main__":
    unittest.main()