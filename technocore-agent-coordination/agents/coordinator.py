from technocore.signer import create_identity
from technocore.mailbox import AgentMailbox


class Coordinator:
    def __init__(self, mailbox: AgentMailbox):
        self.identity = create_identity("coordinator")
        self.mailbox = mailbox

    def assign_task(self, researcher_did: str, task: str):
        return self.mailbox.send(
            self.identity,
            researcher_did,
            f"TASK: {task}",
        )