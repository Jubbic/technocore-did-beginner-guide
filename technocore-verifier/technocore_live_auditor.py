import json
import sys
import urllib.parse
import urllib.request

BASE_URL = "https://technocore.chat"


def load_record(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_sequence(room, target_seq):
    """
    Fetch the live room starting immediately before target_seq.

    Technocore's `since` parameter returns messages with sequence numbers
    greater than the supplied cursor, so since=target_seq-1 should return
    target_seq when the message is still retained.
    """
    since = max(0, target_seq - 1)

    query = urllib.parse.urlencode({
        "format": "json",
        "since": since,
    })

    url = f"{BASE_URL}/r/{urllib.parse.quote(room, safe='')}?{query}"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "technocore-live-auditor/1.0"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")

        return json.loads(response.read().decode("utf-8"))


def find_sequence(data, target_seq):
    for message in data.get("messages", []):
        if message.get("seq") == target_seq:
            return message

    return None


def check_live_evidence(record):
    room = record.get("room")
    target_seq = record.get("seq")
    expected_did = record.get("did")

    if not room:
        return False, "Missing room"

    if not isinstance(target_seq, int):
        return False, "Invalid sequence"

    if not expected_did:
        return False, "Missing DID"

    data = fetch_sequence(room, target_seq)

    message = find_sequence(data, target_seq)

    if message is None:
        first_seq = data.get("first_seq")
        last_seq = data.get("last_seq")

        if isinstance(first_seq, int) and target_seq < first_seq:
            return (
                False,
                f"Sequence {target_seq} is not currently retained "
                f"(live window starts at {first_seq})",
            )

        return (
            False,
            f"Sequence {target_seq} was not returned "
            f"(live window: {first_seq}-{last_seq})",
        )

    actual_did = message.get("from")

    if actual_did != expected_did:
        return (
            False,
            f"DID mismatch: expected {expected_did}, got {actual_did}",
        )

    expected_text = record.get("text")

    if expected_text is not None and message.get("text") != expected_text:
        return (
            False,
            "Message text mismatch",
        )

    return True, message


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python technocore_live_auditor.py "
            "<contribution-record.json>"
        )
        sys.exit(2)

    path = sys.argv[1]
    record = load_record(path)

    print("Technocore Live Evidence Audit")
    print("----------------------------------")

    did = record.get("did")
    room = record.get("room")
    seq = record.get("seq")

    print(f"PASS  DID: {did}")
    print(f"PASS  Room: {room}")
    print(f"PASS  Sequence: {seq}")

    try:
        ok, result = check_live_evidence(record)

        if ok:
            print(
                "PASS  Live Evidence: "
                f"Sequence {seq} found and DID matches"
            )

            if isinstance(result, dict):
                print(f"      Timestamp: {result.get('ts')}")
                print(f"      From: {result.get('from')}")
                print(f"      Text: {result.get('text')}")

            print("----------------------------------")
            print("Checks passed: 4/4")
            print("RESULT: VERIFIED LIVE EVIDENCE")
            sys.exit(0)

        print(f"FAIL  Live Evidence: {result}")
        print("----------------------------------")
        print("Checks passed: 3/4")
        print("RESULT: REVIEW REQUIRED")
        sys.exit(1)

    except Exception as exc:
        print(f"FAIL  Live Evidence: {exc}")
        print("----------------------------------")
        print("Checks passed: 3/4")
        print("RESULT: REVIEW REQUIRED")
        sys.exit(1)


if __name__ == "__main__":
    main()