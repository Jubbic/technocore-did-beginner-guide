from __future__ import annotations

from technocore.signer import AgentIdentity, verify_message


class AgentMailbox:
    def __init__(self):
        self.messages = []

    def send(
        self,
        sender: AgentIdentity,
        recipient: str,
        message: str,
        room: str = "agent-team",
    ) -> dict:

        signed_message = sender.sign(room, message)

        signed_message["recipient"] = recipient

        self.messages.append(signed_message)

        return signed_message

    def receive(self, recipient: str) -> list[dict]:
        return [
            message
            for message in self.messages
            if message["recipient"] == recipient
        ]

    def verify(self, message: dict) -> bool:
        return verify_message(message)

    def all_messages(self) -> list[dict]:
        return list(self.messages)