\# Technocore Spark Market



A public task coordination marketplace powered by signed Technocore messages.



\## Overview



Technocore Spark Market demonstrates how a public coordination marketplace can be built on top of the Technocore signed-message protocol.



Instead of relying on a private database, the application uses a public Technocore room as its event source.



Room:



`d-jubbic-spark`



The application reads the public room, verifies message signatures, reconstructs task state, and displays the resulting marketplace.



\## Task Lifecycle



Tasks follow a simple event-based lifecycle:



`CREATE → CLAIM → COMPLETE → VERIFY`



\### Create



```text

TASK\_CREATE|task-id|reward|description



Creates a new task with a SPARK reputation reward.



Claim



TASK\_CLAIM|task-id|did



Records the DID claiming the task.



Complete

TASK\_COMPLETE|task-id|did|proof



Records completion and provides proof of the work.



Verify



The verifier reads the public room history and:



validates message signatures

validates Technocore DIDs

reconstructs task state

identifies invalid or incomplete events

reports completed tasks and SPARK totals

Public Web App



The web application provides:



live task statistics

open, claimed, and completed tasks

SPARK totals

contributor DIDs

task proofs

public event history

cryptographic signature verification

automatic refresh of public data



The frontend is served from:



web/index.html



The API is implemented in:



web/api/market.py



A local development server is available through:



web/server.py

Run Locally



From the project root:



python .\\web\\server.py



Then open:



http://127.0.0.1:8000



The API is available at:



http://127.0.0.1:8000/api/market

Command Line Marketplace



The command-line marketplace is implemented in:



spark\_market.py



Examples:



python .\\spark\_market.py room



Create a task:



python .\\spark\_market.py create task-002 50 "Build another public verifier test"



Claim a task:



python .\\spark\_market.py claim task-002



Complete a task:



python .\\spark\_market.py complete task-002 "Proof of implementation"

Verification



Run:



python .\\verify.py



The verifier checks the public room and reconstructs the marketplace state from signed events.



Security Model



Private Technocore identity keys must never be uploaded to the web application or committed to Git.



The public application only needs public message data and public DIDs for verification.



Future interactive browser functionality should sign actions locally and send only the signed public event to Technocore.



SPARK



SPARK is a demonstration reputation credit used by this project.



It is not an official FLOP token, cryptocurrency, or monetary asset.



The marketplace is an experimental demonstration of signed public task coordination.



Contribution #8



This project was created as a Technocore Contribution #8 experiment demonstrating a public task marketplace backed by signed Technocore events.



Public room:



d-jubbic-spark



The implementation includes the marketplace event model, public verifier, command-line interface, and read-only web marketplace.





Save and close Notepad.



Then run:



```powershell

git add .\\technocore-spark-market\\README.md

