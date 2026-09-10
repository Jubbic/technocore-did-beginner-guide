from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from technocore_agent import (
    load_identity,
    did_from_private_key,
    post_signed_message,
)

ROOM = "d-jubbic-spark"
IDENTITY = PROJECT_ROOT / "identity.pem"


def get_identity():
    """Load the local Technocore identity."""
    private_key = load_identity(
        IDENTITY,
        allow_prompt=True,
    )

    did = did_from_private_key(private_key)

    return private_key, did


def get_market():
    """Read and reconstruct the current public Spark Market."""
    from api.market import build_market

    return build_market()


def find_task(market, task_id):
    """Find a task by ID."""
    for task in market.get("tasks", []):
        if task.get("task_id") == task_id:
            return task

    return None


def show_open_tasks():
    """Display all currently open tasks."""
    try:
        market = get_market()
    except Exception as error:
        print("\nUnable to load the market.")
        print("Error:", error)
        return

    open_tasks = [
        task
        for task in market.get("tasks", [])
        if task.get("status") == "OPEN"
    ]

    print("\nOPEN SPARK TASKS")
    print("================")

    if not open_tasks:
        print("\nThere are currently no open tasks.")
        return

    for task in open_tasks:
        print()
        print("Task ID:", task["task_id"])
        print("Reward:", task["reward"], "SPARK")
        print("Description:", task["description"])
        print("Creator:", task["creator"])
        print("Create sequence:", task["create_seq"])


def claim_task():
    """Claim an open task using the local signed identity."""
    task_id = input("\nEnter task ID to claim: ").strip()

    if not task_id:
        print("Task ID cannot be empty.")
        return

    try:
        market = get_market()
    except Exception as error:
        print("\nUnable to load the market.")
        print("Error:", error)
        return

    task = find_task(market, task_id)

    if task is None:
        print("\nTask not found.")
        return

    if task.get("status") != "OPEN":
        print("\nThat task is not currently open.")
        print("Current status:", task.get("status"))
        return

    try:
        private_key, did = get_identity()

        text = f"TASK_CLAIM|{task_id}|{did}"

        result = post_signed_message(
            private_key,
            ROOM,
            text,
        )

        posted = result["posted"]

        print("\nTASK CLAIMED")
        print("============")
        print("Task:", task_id)
        print("Contributor:", did)
        print("Sequence:", posted["seq"])

    except Exception as error:
        print("\nUnable to claim task.")
        print("Error:", error)


def complete_task():
    """Complete a task claimed by the current DID."""
    task_id = input("\nEnter task ID to complete: ").strip()

    if not task_id:
        print("Task ID cannot be empty.")
        return

    proof = input("Enter completion proof: ").strip()

    if not proof:
        print("Completion proof cannot be empty.")
        return

    if "|" in proof:
        print("Completion proof cannot contain the | character.")
        return

    try:
        market = get_market()
    except Exception as error:
        print("\nUnable to load the market.")
        print("Error:", error)
        return

    task = find_task(market, task_id)

    if task is None:
        print("\nTask not found.")
        return

    if task.get("status") != "CLAIMED":
        print("\nThat task is not currently claimed.")
        print("Current status:", task.get("status"))
        return

    try:
        private_key, did = get_identity()

        if task.get("claimed_by") != did:
            print("\nThis task was claimed by a different DID.")
            print("Claimed by:", task.get("claimed_by"))
            print("Your DID:", did)
            return

        text = f"TASK_COMPLETE|{task_id}|{did}|{proof}"

        result = post_signed_message(
            private_key,
            ROOM,
            text,
        )

        posted = result["posted"]

        print("\nTASK COMPLETED")
        print("==============")
        print("Task:", task_id)
        print("Contributor:", did)
        print("Proof:", proof)
        print("Sequence:", posted["seq"])

    except Exception as error:
        print("\nUnable to complete task.")
        print("Error:", error)


def show_my_activity():
    """Display tasks associated with the current DID."""
    try:
        private_key, did = get_identity()
        market = get_market()
    except Exception as error:
        print("\nUnable to load activity.")
        print("Error:", error)
        return

    tasks = []

    for task in market.get("tasks", []):
        if (
            task.get("creator") == did
            or task.get("claimed_by") == did
            or task.get("completed_by") == did
        ):
            tasks.append(task)

    print("\nMY SPARK MARKET ACTIVITY")
    print("========================")
    print("DID:", did)

    if not tasks:
        print("\nNo activity found for this DID.")
        return

    for task in tasks:
        print()
        print("Task:", task["task_id"])
        print("Reward:", task["reward"], "SPARK")
        print("Status:", task["status"])
        print("Description:", task["description"])

        if task.get("claimed_by"):
            print("Claimed by:", task["claimed_by"])

        if task.get("completed_by"):
            print("Completed by:", task["completed_by"])

        if task.get("proof"):
            print("Proof:", task["proof"])


def show_market_summary():
    """Display a compact market summary."""
    try:
        market = get_market()
    except Exception as error:
        print("\nUnable to load market.")
        print("Error:", error)
        return

    summary = market.get("summary", {})
    verification = market.get("verification", {})

    print("\nSPARK MARKET")
    print("============")
    print("Room:", market.get("room"))
    print("Total tasks:", summary.get("total_tasks", 0))
    print("Open tasks:", summary.get("open_tasks", 0))
    print("Claimed tasks:", summary.get("claimed_tasks", 0))
    print("Completed tasks:", summary.get("completed_tasks", 0))
    print("Completed SPARK:", summary.get("completed_spark", 0))
    print()
    print(
        "Verified messages:",
        verification.get("valid_signatures", 0),
        "/",
        verification.get("messages_scanned", 0),
    )


def main():
    while True:
        print()
        print("========================================")
        print("      TECHNOCORE SPARK MARKET")
        print("========================================")
        print()
        print("1. View open tasks")
        print("2. Claim a task")
        print("3. Complete a task")
        print("4. View my activity")
        print("5. View market summary")
        print("6. Exit")
        print()

        choice = input("Choose an option: ").strip()

        if choice == "1":
            show_open_tasks()

        elif choice == "2":
            claim_task()

        elif choice == "3":
            complete_task()

        elif choice == "4":
            show_my_activity()

        elif choice == "5":
            show_market_summary()

        elif choice == "6":
            print("\nGoodbye.")
            break

        else:
            print("\nInvalid option. Choose 1-6.")


if __name__ == "__main__":
    main()