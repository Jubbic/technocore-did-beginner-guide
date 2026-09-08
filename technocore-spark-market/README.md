# Technocore SPARK Market

> Contribution #8 — Public signed task coordination marketplace built on Technocore.

**Live application:** https://jubbic-spark-market-2026.vercel.app

**Public Technocore room:** `d-jubbic-spark`

---

## Overview

Technocore SPARK Market is a public task coordination marketplace built around signed Technocore messages.

Instead of relying on a private database to determine task state, the marketplace reconstructs task lifecycles directly from events published to a public Technocore room.

Every event is cryptographically verified before it is used to update marketplace state.

The current implementation demonstrates the complete lifecycle:

```text
CREATE → CLAIM → COMPLETE → VERIFY
What It Demonstrates

The project demonstrates how a public signed-message layer can be used to coordinate tasks without requiring a centralized task database.

A task can be:

Created publicly.
Claimed by a contributor.
Marked complete with proof.
Reconstructed and verified by independent software.

The public room acts as the event source.

The web application reads those events, verifies their signatures, reconstructs the current state of each task, and displays the result.

Architecture
                    Technocore Public Room
                           │
                           │ signed events
                           ▼
                 ┌─────────────────────┐
                 │  d-jubbic-spark     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Python API          │
                 │                     │
                 │ • Fetch events      │
                 │ • Verify signatures │
                 │ • Rebuild state     │
                 └──────────┬──────────┘
                            │
                            │ JSON
                            ▼
                 ┌─────────────────────┐
                 │ SPARK Market        │
                 │ Dashboard           │
                 └─────────────────────┘

The dashboard does not trust task state blindly.

It receives verified public events and derives the marketplace state from them.

Event Protocol

SPARK Market currently uses three task event types.

Task creation
TASK_CREATE|task-id|reward|description

Example:

TASK_CREATE|task-001|30|Build a public verifier for Technocore Spark Market task events
Task claim
TASK_CLAIM|task-id|did

Example:

TASK_CLAIM|task-001|did:key:z6MksazjmAFoVhiQfbDVEhtFgJ5kKPuDTYS3mGZr5iNZzpzZ
Task completion
TASK_COMPLETE|task-id|did|proof

Example:

TASK_COMPLETE|task-001|did:key:z6MksazjmAFoVhiQfbDVEhtFgJ5kKPuDTYS3mGZr5iNZzpzZ|Public verifier implemented and tested against the d-jubbic-spark room
Verification Model

Before an event is used by the marketplace, the verifier checks its cryptographic signature.

The implementation:

Extracts the sender DID.
Extracts the signature and nonce.
Reconstructs the signed message payload.
Derives the Ed25519 public key from the DID.
Verifies the signature.
Rejects events that fail verification.
Reconstructs task state only from valid events.

This allows an independent observer to verify that marketplace events were actually signed by the DID that published them.

Current Public Proof

The public room currently contains four signed messages.

Sequence	Event	Result
1	Market launch announcement	Valid
2	TASK_CREATE	Valid
3	TASK_CLAIM	Valid
4	TASK_COMPLETE	Valid

Current verification result:

Messages scanned: 4
Valid signatures: 4
Invalid signatures: 0
Tasks found: 1
Open tasks: 0
Claimed tasks: 0
Completed tasks: 1
Completed SPARK: 30

Task task-001 completed successfully through the public event lifecycle.

Public Room

Room:

d-jubbic-spark

The room contains the signed events used to construct the current marketplace state.

The project intentionally keeps the event source public so that the displayed task state can be independently inspected.

Web Application

The production dashboard provides:

Total task count
Open task count
Completed task count
Completed SPARK
Task lifecycle information
Creator and contributor DIDs
Event sequences
Completion proof
Cryptographic verification status
Live public activity
Automatic data refresh

The dashboard is read-only in the current version.

This means users can inspect and verify public marketplace state without the application needing access to private identity material.

Local Usage
Requirements
Python 3.12+
The Technocore DID starter project
An existing Technocore identity for publishing events

Install the required dependencies:

pip install -r requirements.txt
Create a Task

From the project directory:

python spark_market.py create task-002 20 "Example task description"

The command publishes a signed TASK_CREATE event to the public room.

Claim a Task
python spark_market.py claim task-002

This publishes a signed TASK_CLAIM event.

Complete a Task
python spark_market.py complete task-002 "Describe the completed work and provide proof"

This publishes a signed TASK_COMPLETE event.

Read the Public Room
python spark_market.py room

This displays the public events currently visible in the SPARK Market room.

Run the Local Verifier

The standalone verifier can be used to inspect and validate marketplace events:

python verify.py

The verifier reconstructs task state and reports signature validity.

Local Web Development

The project also contains a local development web server.

From the project directory:

python web/server.py

Then open:

http://127.0.0.1:8000

The local dashboard reads the market API and displays the reconstructed task state.

Security

Private identity material must never be uploaded to GitHub or deployed to Vercel.

The project excludes:

identity.pem
identity.pem.txt

from version control.

The production dashboard does not require the user's private key.

Cryptographic verification is performed using the public information contained in the signed events and their DIDs.

SPARK Disclaimer

SPARK is a demonstration reputation credit used by this project to represent task value.

It is not an official FLOP token, Technocore token, cryptocurrency, or financial asset.

The numbers displayed by the marketplace represent the project's demonstration task/reputation system.

Project Structure
technocore-spark-market/
│
├── contribution-8-proof.json
├── create_spark_room.py
├── README.md
├── rules.md
├── spark_market.py
├── verify.py
│
├── demo/
│   └── index.html
│
└── web/
    ├── index.html
    ├── server.py
    │
    └── api/
        └── market.py

The production deployment also uses the repository-level Vercel files:

index.html
api/
├── index.py
pyproject.toml
requirements.txt
vercel.json
Contribution #8

This contribution demonstrates a complete public signed-task coordination flow using Technocore:

Public Room
     ↓
Signed Event
     ↓
Cryptographic Verification
     ↓
Task State Reconstruction
     ↓
Public Marketplace

The implementation combines:

Signed Technocore messages
DID-based identity
Ed25519 signature verification
Public event reconstruction
Task lifecycle management
A Python API
A browser dashboard
Public deployment on Vercel

The result is a publicly inspectable demonstration of task coordination built around signed events rather than a private centralized task database.

Status

Contribution #8: Complete

Current public verification:

4/4 signatures valid
1/1 tasks completed
30 SPARK completed
0 invalid signatures
0 verification errors

Live: https://jubbic-spark-market-2026.vercel.app


### Step 2 — Save it

In Notepad:

**File → Save**

Then close Notepad.

### Step 3 — Check the README

Run:

```powershell
Get-Content technocore-spark-market\README.md