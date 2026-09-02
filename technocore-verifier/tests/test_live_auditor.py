import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from technocore_live_auditor import check_live_evidence


DID = "did:key:z6MksazjmAFoVhiQfbDVEhtFgJ5kKPuDTYS3mGZr5iNZzpzZ"
ROOM = "d-jubbic-builders"


class TestLiveAuditor(unittest.TestCase):

    def test_matching_live_evidence(self):
        record = {
            "did": DID,
            "room": ROOM,
            "seq": 1,
            "text": "Jubbic Builders room is live.",
        }

        live_data = {
            "room": ROOM,
            "first_seq": 1,
            "last_seq": 1,
            "messages": [
                {
                    "seq": 1,
                    "ts": "2026-09-02T14:22:21.583073Z",
                    "from": DID,
                    "text": "Jubbic Builders room is live.",
                    "nonce": 123,
                    "sig": "test-signature",
                }
            ],
        }

        with patch(
            "technocore_live_auditor.fetch_sequence",
            return_value=live_data,
        ):
            ok, result = check_live_evidence(record)

        self.assertTrue(ok)
        self.assertEqual(result["seq"], 1)
        self.assertEqual(result["from"], DID)

    def test_did_mismatch(self):
        record = {
            "did": DID,
            "room": ROOM,
            "seq": 1,
        }

        live_data = {
            "room": ROOM,
            "first_seq": 1,
            "last_seq": 1,
            "messages": [
                {
                    "seq": 1,
                    "from": "did:key:wrong",
                    "text": "test",
                }
            ],
        }

        with patch(
            "technocore_live_auditor.fetch_sequence",
            return_value=live_data,
        ):
            ok, result = check_live_evidence(record)

        self.assertFalse(ok)
        self.assertIn("DID mismatch", result)

    def test_sequence_not_retained(self):
        record = {
            "did": DID,
            "room": "technocore",
            "seq": 100,
        }

        live_data = {
            "room": "technocore",
            "first_seq": 500,
            "last_seq": 549,
            "messages": [],
        }

        with patch(
            "technocore_live_auditor.fetch_sequence",
            return_value=live_data,
        ):
            ok, result = check_live_evidence(record)

        self.assertFalse(ok)
        self.assertIn("not currently retained", result)

    def test_message_text_mismatch(self):
        record = {
            "did": DID,
            "room": ROOM,
            "seq": 1,
            "text": "Expected message",
        }

        live_data = {
            "room": ROOM,
            "first_seq": 1,
            "last_seq": 1,
            "messages": [
                {
                    "seq": 1,
                    "from": DID,
                    "text": "Different message",
                }
            ],
        }

        with patch(
            "technocore_live_auditor.fetch_sequence",
            return_value=live_data,
        ):
            ok, result = check_live_evidence(record)

        self.assertFalse(ok)
        self.assertEqual(result, "Message text mismatch")


if __name__ == "__main__":
    unittest.main()