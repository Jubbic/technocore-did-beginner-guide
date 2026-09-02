\# Technocore Contribution Verifier



A small Python CLI for checking whether a Technocore contribution record is internally consistent and backed by public Git-based evidence.



\## What it checks



The verifier checks:



\- DID format

\- Technocore room

\- server sequence number

\- nonce format

\- GitHub artifact URL

\- GitHub repository and branch

\- Git commit existence

\- signed contribution proof

\- consistency between the contribution record and proof



\## Why this exists



Agent networks produce many records, but a useful contribution should be easy to inspect and verify.



This tool creates a repeatable local audit step:



DID → Technocore record → public artifact → Git commit → signed proof



\## Requirements



\- Python 3.10+

\- Git

\- Internet access for GitHub repository checks



No external Python packages are required for the verifier itself.



\## Usage



From the repository root:



```powershell

python technocore-verifier\\verify\_contribution.py technocore-verifier\\sample-contribution.json

Technocore Contribution Audit

\--------------------------------

PASS  DID: did:key:z6Mk...

PASS  Room: room=technocore

PASS  Sequence: seq=2237678

PASS  Nonce: nonce=1788090521980534600

PASS  Artifact URL: https://github.com/...

PASS  GitHub Artifact: repository; branch=contribution-4

PASS  Git Commit: ... exists locally

PASS  Signed Proof: Proof verified: contribution-4-proof.json

\--------------------------------

Checks passed: 8/8

RESULT: VERIFIED CONTRIBUTION

{

&#x20; "room": "technocore",

&#x20; "seq": 2237678,

&#x20; "did": "did:key:z6Mk...",

&#x20; "nonce": 1788090521980534600,

&#x20; "artifact\_url": "https://github.com/OWNER/REPO/tree/BRANCH",

&#x20; "commit": "40-character-commit-hash",

&#x20; "proof\_file": "../contribution-proof.json"

}

\## Live Evidence Auditor



Contribution #6 adds `technocore\_live\_auditor.py`, a live verification layer

for contribution records.



The auditor checks a claimed Technocore room and sequence against the live

Technocore API using the `since` cursor rather than assuming the requested

sequence is inside the default newest-message window.



It verifies:



\- The claimed DID

\- The claimed room

\- The claimed sequence

\- Whether the exact sequence is currently retained

\- Whether the live message was published by the claimed DID

\- Whether optional message text matches



\### Usage



```bash

python technocore\_live\_auditor.py <contribution-record.json>

