from agents.coordinator import Coordinator
from agents.researcher import Researcher
from agents.developer import Developer
from agents.reviewer import Reviewer
from technocore.mailbox import AgentMailbox
from llm import LLMClient


def main():
    mailbox = AgentMailbox()
    llm = LLMClient()

    coordinator = Coordinator(mailbox)
    researcher = Researcher(mailbox, llm)
    developer = Developer(mailbox, llm)
    reviewer = Reviewer(mailbox, llm)

    print("\n=== TECHNCORE AGENT COORDINATION DEMO ===\n")

    print("Agent identities:")
    print("Coordinator:", coordinator.identity.did)
    print("Researcher :", researcher.identity.did)
    print("Developer  :", developer.identity.did)
    print("Reviewer   :", reviewer.identity.did)

    task = "Design a simple API health-check service."

    print("\n--- 1. Coordinator assigns task ---")

    task_message = coordinator.assign_task(
        researcher.identity.did,
        task,
    )

    print("Signed:", mailbox.verify(task_message))
    print("Message:", task_message["message"])

    print("\n--- 2. Researcher analyzes the task ---")

    research_message = researcher.research(
        task,
        developer.identity.did,
    )

    print("Signed:", mailbox.verify(research_message))
    print("Message:", research_message["message"])

    print("\n--- 3. Developer proposes implementation ---")

    implementation_message = developer.implement(
        research_message["message"],
        reviewer.identity.did,
    )

    print("Signed:", mailbox.verify(implementation_message))
    print("Message:", implementation_message["message"])

    print("\n--- 4. Reviewer evaluates implementation ---")

    review_message = reviewer.review(
        implementation_message["message"],
        coordinator.identity.did,
    )

    print("Signed:", mailbox.verify(review_message))
    print("Message:", review_message["message"])

    print("\n=== MESSAGE AUDIT ===")

    for number, message in enumerate(
        mailbox.all_messages(),
        start=1,
    ):
        print(
            f"{number}. "
            f"{message['agent']} -> "
            f"{message['recipient']} | "
            f"verified={mailbox.verify(message)}"
        )


if __name__ == "__main__":
    main()