import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE_URL = "https://technocore.chat"


def fetch_room(room, since=None):
    """Fetch the current retained room window or messages after a cursor."""
    params = {"format": "json"}

    if since is not None:
        params["since"] = since

    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/r/{urllib.parse.quote(room, safe='')}?{query}"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "technocore-room-snapshot/1.0"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")

        return json.loads(response.read().decode("utf-8"))


def analyse_messages(messages):
    """Check sequence continuity and duplicate sequence numbers."""
    sequences = [
        message.get("seq")
        for message in messages
        if isinstance(message.get("seq"), int)
    ]

    duplicates = sorted(
        {
            seq
            for seq in sequences
            if sequences.count(seq) > 1
        }
    )

    gaps = []

    for previous, current in zip(sequences, sequences[1:]):
        if current > previous + 1:
            gaps.extend(range(previous + 1, current))

    return {
        "sequence_count": len(sequences),
        "duplicates": duplicates,
        "gaps": gaps,
    }


def canonical_snapshot(snapshot):
    """Create deterministic JSON for hashing."""
    return json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def create_snapshot(room, data):
    """Build a reproducible room integrity snapshot."""
    messages = data.get("messages", [])

    analysis = analyse_messages(messages)

    snapshot = {
        "schema": "technocore-room-snapshot-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "room": room,
        "first_seq": data.get("first_seq"),
        "last_seq": data.get("last_seq"),
        "message_count": len(messages),
        "sequence_count": analysis["sequence_count"],
        "sequence_gaps": analysis["gaps"],
        "duplicate_sequences": analysis["duplicates"],
        "messages": messages,
    }

    digest = hashlib.sha256(
        canonical_snapshot(snapshot)
    ).hexdigest()

    snapshot["snapshot_sha256"] = digest

    return snapshot


def print_report(snapshot):
    """Print a human-readable integrity report."""
    print("Technocore Room Integrity Snapshot")
    print("----------------------------------")
    print(f"Room: {snapshot['room']}")
    print(f"First sequence: {snapshot['first_seq']}")
    print(f"Last sequence: {snapshot['last_seq']}")
    print(f"Messages captured: {snapshot['message_count']}")
    print(f"Sequence records: {snapshot['sequence_count']}")

    if snapshot["sequence_gaps"]:
        print(
            f"Sequence gaps: {len(snapshot['sequence_gaps'])}"
        )
    else:
        print("Sequence gaps: NONE")

    if snapshot["duplicate_sequences"]:
        print(
            "Duplicate sequences: "
            f"{snapshot['duplicate_sequences']}"
        )
    else:
        print("Duplicate sequences: NONE")

    print("----------------------------------")
    print(f"SHA-256: {snapshot['snapshot_sha256']}")

    if (
        not snapshot["sequence_gaps"]
        and not snapshot["duplicate_sequences"]
    ):
        print("RESULT: INTEGRITY CHECK PASSED")
    else:
        print("RESULT: REVIEW REQUIRED")


def main():
    parser = argparse.ArgumentParser(
        description="Create a verifiable snapshot of a Technocore room."
    )

    parser.add_argument(
        "room",
        help="Technocore room name",
    )

    parser.add_argument(
        "--since",
        type=int,
        default=None,
        help="Only retrieve messages after this sequence cursor",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Write the snapshot to a JSON file",
    )

    args = parser.parse_args()

    try:
        data = fetch_room(args.room, args.since)

        snapshot = create_snapshot(
            args.room,
            data,
        )

        print_report(snapshot)

        if args.output:
            with open(
                args.output,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    snapshot,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            print(f"Snapshot saved: {args.output}")

        if (
            snapshot["sequence_gaps"]
            or snapshot["duplicate_sequences"]
        ):
            raise SystemExit(1)

    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()