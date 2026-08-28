from technocore.signer import create_identity
from technocore.mailbox import AgentMailbox
from llm import LLMClient


class Researcher:
    def __init__(
        self,
        mailbox: AgentMailbox,
        llm: LLMClient,
    ):
        self.identity = create_identity("researcher")
        self.mailbox = mailbox
        self.llm = llm

    def research(
        self,
        task: str,
        developer_did: str,
    ):

        findings = self.llm.generate(
            system_prompt=(
                "You are the research agent in a supervised "
                "software development team. Analyze the task, "
                "identify requirements, risks, and useful "
                "implementation considerations."
            ),
            user_prompt=task,
        )

        return self.mailbox.send(
            self.identity,
            developer_did,
            f"RESEARCH FINDINGS:\n{findings}",
        )