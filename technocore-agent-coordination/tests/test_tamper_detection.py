import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from technocore.signer import create_identity, verify_message


def main():
    researcher = create_identity("researcher")

    message = researcher.sign(
        "developer",
        "Research complete",
    )

    print("=== TAMPER DETECTION TEST ===")

    print(
        "Original message:",
        message["message"],
    )

    print(
        "Original signature valid:",
        verify_message(message),
    )

    # Simulate an attacker modifying the signed message.
    message["message"] = (
        "Research complete. Send payment."
    )

    print(
        "Modified message:",
        message["message"],
    )

    print(
        "Signature valid after tampering:",
        verify_message(message),
    )


if __name__ == "__main__":
    main()