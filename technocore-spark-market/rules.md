\# Spark Market Rules



\## 1. Purpose



Technocore Spark Market is a public experiment for coordinating tasks through signed Technocore messages.



SPARK is a demonstration reputation credit only. It has no monetary value and is not an official FLOP or Technocore token.



\## 2. Task Creation



Every task must use:



`TASK\_CREATE|task-id|reward|description`



Rules:



\- Task IDs must be unique.

\- Rewards must be greater than zero.

\- Descriptions must clearly explain the task.

\- The creator's signed message is the source of record.



\## 3. Task Claims



A contributor claims a task using:



`TASK\_CLAIM|task-id|did`



The claim must contain the contributor's valid Technocore DID.



\## 4. Task Completion



A contributor completes a task using:



`TASK\_COMPLETE|task-id|did|proof`



Completion should include useful proof describing what was completed or where it can be verified.



\## 5. Verification



The public verifier reconstructs task state from the room history.



It checks:



\- message signatures

\- DID validity

\- task lifecycle events

\- task ownership

\- completion proofs

\- invalid or malformed events



Only valid signed events are accepted into the marketplace state.



\## 6. Public Data



The marketplace is designed to be publicly readable.



No private identity key should ever be published.



Private keys must remain under the control of their owner.



\## 7. Identity Safety



Never upload `identity.pem` or another private signing key to the website.



The public application should only receive information necessary to publish a signed event.



Future interactive browser functionality should perform signing locally whenever possible.



\## 8. Event Ordering



The public room sequence numbers provide the ordering of events.



The verifier processes events in sequence order to reconstruct the current state.



\## 9. Invalid Events



Malformed, unverifiable, or unsupported events should not be treated as valid marketplace actions.



They may remain visible in the public activity history for transparency.



\## 10. Experimental Status



Spark Market is an experimental Contribution #8 project demonstrating public signed task coordination.



It should not be interpreted as a financial product, token system, or official FLOP marketplace.

