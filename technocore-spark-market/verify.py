from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from technocore_agent import (
    read_room,
    message_payload,
    verify_bytes,
)

ROOM = "d-jubbic-spark"


def verify_message(message):
    """
    Verify one Technocore room message using the exact
    Technocore signing protocol:

        room|nonce|text

    The message signature is stored in the `sig` field.
    """

    did = message.get("from")
    signature = message.get("sig")
    nonce = message.get("nonce")
    text = message.get("text")

    if not isinstance(did, str):
        return False, "missing/invalid DID"

    if not isinstance(signature, str):
        return False, "missing/invalid signature"

    if nonce is None:
        return False, "missing nonce"

    if not isinstance(text, str):
        return False, "missing/invalid text"

    try:
        normalized, payload = message_payload(
            ROOM,
            nonce,
            text,
        )

        # The server signs the normalized text.
        if normalized != text:
            return False, "text is not normalized"

        # Exact protocol:
        # verify_bytes(did, signature, payload)
        verify_bytes(
            did,
            signature,
            payload,
        )

        return True, "valid"

    except Exception as exc:
        return False, str(exc)


def parse_event(text):
    """
    Parse recognized Spark Market events.
    """

    parts = text.split("|")

    if not parts:
        return None

    event_type = parts[0]

    if event_type == "TASK_CREATE" and len(parts) == 4:
        task_id = parts[1]

        try:
            reward = int(parts[2])
        except ValueError:
            return None

        description = parts[3]

        return {
            "type": "TASK_CREATE",
            "task_id": task_id,
            "reward": reward,
            "description": description,
        }

    if event_type == "TASK_CLAIM" and len(parts) == 3:
        return {
            "type": "TASK_CLAIM",
            "task_id": parts[1],
            "did": parts[2],
        }

    if event_type == "TASK_COMPLETE" and len(parts) == 4:
        return {
            "type": "TASK_COMPLETE",
            "task_id": parts[1],
            "did": parts[2],
            "proof": parts[3],
        }

    return None


def verify_market():
    data = read_room(
        ROOM,
        limit=200,
        cache_buster=__import__("time").time_ns(),
    )

    messages = data["messages"]

    tasks = {}

    valid_signatures = 0
    invalid_signatures = 0
    ignored_events = 0

    print()
    print("TECHNOCORE SPARK MARKET VERIFIER")
    print("================================")
    print("Room:", ROOM)
    print("Messages scanned:", len(messages))
    print()

    for message in messages:

        seq = message.get("seq")
        text = message.get("text", "")

        valid, reason = verify_message(message)

        if valid:
            valid_signatures += 1
            signature_status = "VALID"
        else:
            invalid_signatures += 1
            signature_status = "INVALID"

        print(
            f"[SEQ {seq}] "
            f"Signature: {signature_status}"
        )

        if not valid:
            print("  Reason:", reason)

        # Never process an event whose signature failed.
        if not valid:
            continue

        event = parse_event(text)

        if event is None:
            ignored_events += 1
            continue

        event_type = event["type"]
        task_id = event["task_id"]

        if event_type == "TASK_CREATE":

            tasks[task_id] = {
                "task_id": task_id,
                "reward": event["reward"],
                "description": event["description"],
                "creator": message.get("from"),
                "create_seq": seq,
                "status": "OPEN",
                "claimed_by": None,
                "claim_seq": None,
                "completed_by": None,
                "complete_seq": None,
                "proof": None,
            }

        elif event_type == "TASK_CLAIM":

            task = tasks.get(task_id)

            if task is None:
                ignored_events += 1
                continue

            task["status"] = "CLAIMED"
            task["claimed_by"] = event["did"]
            task["claim_seq"] = seq

        elif event_type == "TASK_COMPLETE":

            task = tasks.get(task_id)

            if task is None:
                ignored_events += 1
                continue

            task["status"] = "COMPLETED"
            task["completed_by"] = event["did"]
            task["complete_seq"] = seq
            task["proof"] = event["proof"]

    completed_spark = sum(
        task["reward"]
        for task in tasks.values()
        if task["status"] == "COMPLETED"
    )

    open_tasks = sum(
        1
        for task in tasks.values()
        if task["status"] == "OPEN"
    )

    claimed_tasks = sum(
        1
        for task in tasks.values()
        if task["status"] == "CLAIMED"
    )

    completed_tasks = sum(
        1
        for task in tasks.values()
        if task["status"] == "COMPLETED"
    )

    print()
    print("TASKS")
    print("-----")

    if not tasks:
        print("No valid tasks found.")
    else:
        for task in tasks.values():

            print()
            print("Task ID:", task["task_id"])
            print("Reward:", task["reward"], "SPARK")
            print("Description:", task["description"])
            print("Creator:", task["creator"])
            print("Status:", task["status"])

            if task["claimed_by"]:
                print("Claimed by:", task["claimed_by"])
                print("Claim sequence:", task["claim_seq"])

            if task["completed_by"]:
                print("Completed by:", task["completed_by"])
                print("Completion sequence:", task["complete_seq"])
                print("Proof:", task["proof"])

    print()
    print("VERIFICATION SUMMARY")
    print("--------------------")
    print("Messages scanned:", len(messages))
    print("Valid signatures:", valid_signatures)
    print("Invalid signatures:", invalid_signatures)
    print("Tasks found:", len(tasks))
    print("Open tasks:", open_tasks)
    print("Claimed tasks:", claimed_tasks)
    print("Completed tasks:", completed_tasks)
    print("Completed SPARK:", completed_spark)
    print("Ignored invalid events:", ignored_events)

    if invalid_signatures == 0:
        print()
        print("RESULT: ALL SIGNATURES VALID")
    else:
        print()
        print("RESULT: SIGNATURE VERIFICATION FAILED")

    return invalid_signatures == 0


if __name__ == "__main__":
    success = verify_market()

    if not success:
        raise SystemExit(1)