from pathlib import Path
import sys
import argparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from technocore_agent import (
    load_identity,
    did_from_private_key,
    post_signed_message,
    read_room,
)


ROOM = "d-jubbic-spark"
IDENTITY = PROJECT_ROOT / "identity.pem"


def get_identity():
    private_key = load_identity(
        IDENTITY,
        allow_prompt=True,
    )
    did = did_from_private_key(private_key)
    return private_key, did


def create_task(task_id, reward, description):
    private_key, did = get_identity()

    if reward <= 0:
        raise ValueError("Reward must be greater than zero.")

    if "|" in task_id or "|" in description:
        raise ValueError("Task ID and description cannot contain |")

    text = (
        f"TASK_CREATE|{task_id}|{reward}|{description}"
    )

    result = post_signed_message(
        private_key,
        ROOM,
        text,
    )

    print("\nTASK CREATED")
    print("-------------")
    print("Task ID:", task_id)
    print("Reward:", reward, "SPARK")
    print("Creator:", did)
    print("Room:", ROOM)
    print("Sequence:", result["posted"]["seq"])


def claim_task(task_id):
    private_key, did = get_identity()

    text = f"TASK_CLAIM|{task_id}|{did}"

    result = post_signed_message(
        private_key,
        ROOM,
        text,
    )

    print("\nTASK CLAIMED")
    print("------------")
    print("Task ID:", task_id)
    print("Contributor:", did)
    print("Sequence:", result["posted"]["seq"])


def complete_task(task_id, proof):
    private_key, did = get_identity()

    if "|" in proof:
        raise ValueError("Proof cannot contain |")

    text = (
        f"TASK_COMPLETE|{task_id}|{did}|{proof}"
    )

    result = post_signed_message(
        private_key,
        ROOM,
        text,
    )

    print("\nTASK COMPLETED")
    print("--------------")
    print("Task ID:", task_id)
    print("Contributor:", did)
    print("Proof:", proof)
    print("Sequence:", result["posted"]["seq"])


def show_room():
    data = read_room(
        ROOM,
        limit=200,
        cache_buster=__import__("time").time_ns(),
    )

    print("\nPUBLIC SPARK MARKET ROOM")
    print("------------------------")
    print("Room:", data["room"])
    print("Messages:", data["count"])
    print("First sequence:", data["first_seq"])
    print("Last sequence:", data["last_seq"])

    for message in data["messages"]:
        print(
            f"\n[{message['seq']}] "
            f"{message['from']}\n"
            f"{message['text']}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Technocore Spark Market"
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    create = sub.add_parser("create")
    create.add_argument("task_id")
    create.add_argument("reward", type=int)
    create.add_argument("description")

    claim = sub.add_parser("claim")
    claim.add_argument("task_id")

    complete = sub.add_parser("complete")
    complete.add_argument("task_id")
    complete.add_argument("proof")

    sub.add_parser("room")

    args = parser.parse_args()

    if args.command == "create":
        create_task(
            args.task_id,
            args.reward,
            args.description,
        )

    elif args.command == "claim":
        claim_task(args.task_id)

    elif args.command == "complete":
        complete_task(
            args.task_id,
            args.proof,
        )

    elif args.command == "room":
        show_room()


if __name__ == "__main__":
    main()