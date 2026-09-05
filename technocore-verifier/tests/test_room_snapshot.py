import unittest

from technocore_room_snapshot import analyse_messages, create_snapshot


class TestRoomSnapshot(unittest.TestCase):

    def test_contiguous_sequences(self):
        messages = [
            {"seq": 1, "from": "did:key:test", "text": "one"},
            {"seq": 2, "from": "did:key:test", "text": "two"},
            {"seq": 3, "from": "did:key:test", "text": "three"},
        ]

        result = analyse_messages(messages)

        self.assertEqual(result["sequence_count"], 3)
        self.assertEqual(result["gaps"], [])
        self.assertEqual(result["duplicates"], [])

    def test_detect_sequence_gap(self):
        messages = [
            {"seq": 1},
            {"seq": 2},
            {"seq": 4},
        ]

        result = analyse_messages(messages)

        self.assertEqual(result["gaps"], [3])

    def test_detect_duplicate_sequence(self):
        messages = [
            {"seq": 1},
            {"seq": 2},
            {"seq": 2},
        ]

        result = analyse_messages(messages)

        self.assertEqual(result["duplicates"], [2])

    def test_snapshot_contains_hash(self):
        data = {
            "first_seq": 1,
            "last_seq": 2,
            "messages": [
                {
                    "seq": 1,
                    "from": "did:key:test",
                    "text": "hello",
                },
                {
                    "seq": 2,
                    "from": "did:key:test",
                    "text": "world",
                },
            ],
        }

        snapshot = create_snapshot(
            "test-room",
            data,
        )

        self.assertEqual(
            snapshot["schema"],
            "technocore-room-snapshot-v1",
        )

        self.assertEqual(
            len(snapshot["snapshot_sha256"]),
            64,
        )

        self.assertEqual(
            snapshot["sequence_gaps"],
            [],
        )

        self.assertEqual(
            snapshot["duplicate_sequences"],
            [],
        )


if __name__ == "__main__":
    unittest.main()