from technocore.signer import create_identity
from technocore.mailbox import AgentMailbox
from llm import LLMClient


class Developer:
    def __init__(
        self,
        mailbox: AgentMailbox,
        llm: LLMClient,
    ):
        self.identity = create_identity("developer")
        self.mailbox = mailbox
        self.llm = llm

    def implement(
        self,
        research: str,
        reviewer_did: str,
    ):

        implementation = self.llm.generate(
            system_prompt=(
                "You are the developer agent in a supervised "
                "software team. Use the research provided to "
                "propose a practical implementation."
            ),
            user_prompt=research,
        )

        return self.mailbox.send(
            self.identity,
            reviewer_did,
            f"IMPLEMENTATION:\n{implementation}",
        )