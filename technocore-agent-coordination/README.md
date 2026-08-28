# Technocore Agent Coordination Demo

An experimental demonstration of supervised multi-agent coordination using
Technocore signed messages as the communication layer.

## What This Demonstrates

This project shows how multiple software agents can coordinate through
cryptographically signed messages instead of passing raw model output
directly from one agent to another.

The workflow consists of:

Coordinator
    ↓
Researcher
    ↓
Developer
    ↓
Reviewer
    ↓
Coordinator

Each agent has its own DID-based cryptographic identity.

## Architecture

### Coordinator

Creates and assigns the software task.

### Researcher

Analyzes the task and sends research findings to the Developer.

### Developer

Uses the research to produce an implementation proposal.

### Reviewer

Reviews the implementation and sends the review back to the Coordinator.

## Technocore's Role

Technocore does not generate the software code or replace the LLM.

Instead, it provides the communication and verification layer.

Messages exchanged between agents are:

- associated with agent identities
- cryptographically signed
- delivered through an agent mailbox
- independently verifiable

This creates a verifiable communication boundary between agents.

## LLM Layer

The project includes an `LLMClient` abstraction.

When no API key is configured, the project runs in demo mode so the
coordination and cryptographic workflow can still be tested.

A real LLM provider can be connected later without changing the core
Technocore signing and mailbox architecture.

## Tamper Detection

The project includes a reproducible tamper-detection test.

Run:

```powershell
python tests\test_tamper_detection.py