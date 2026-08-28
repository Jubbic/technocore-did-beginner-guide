from technocore.signer import create_identity
from technocore.mailbox import AgentMailbox
from llm import LLMClient


class Reviewer:
    def __init__(
        self,
        mailbox: AgentMailbox,
        llm: LLMClient,
    ):
        self.identity = create_identity("reviewer")
        self.mailbox = mailbox
        self.llm = llm

    def review(
        self,
        implementation: str,
        coordinator_did: str,
    ):

        review = self.llm.generate(
            system_prompt=(
                "You are the reviewer agent in a supervised "
                "software team. Review the proposed implementation "
                "for correctness, risks, missing requirements, "
                "and practical improvements."
            ),
            user_prompt=implementation,
        )

        return self.mailbox.send(
            self.identity,
            coordinator_did,
            f"REVIEW:\n{review}",
        )