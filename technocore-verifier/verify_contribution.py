#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


DID_PATTERN = re.compile(r"^did:key:z[1-9A-HJ-NP-Za-km-z]+$")
COMMIT_PATTERN = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("JSON file must contain an object")

    return data


def check_did(record: dict) -> tuple[bool, str]:
    did = record.get("did") or record.get("from")

    if not isinstance(did, str):
        return False, "Missing DID"

    if not DID_PATTERN.fullmatch(did):
        return False, f"Invalid DID format: {did}"

    return True, did


def check_room(record: dict) -> tuple[bool, str]:
    room = record.get("room")

    if room != "technocore":
        return False, f"Expected technocore, got {room!r}"

    return True, "room=technocore"


def check_seq(record: dict) -> tuple[bool, str]:
    seq = record.get("seq")

    if not isinstance(seq, int) or seq <= 0:
        return False, "Sequence must be a positive integer"

    return True, f"seq={seq}"


def check_nonce(record: dict) -> tuple[bool, str]:
    nonce = record.get("nonce")

    if isinstance(nonce, int):
        text = str(nonce)
    elif isinstance(nonce, str):
        text = nonce
    else:
        return False, "Missing nonce"

    if not text.isdigit():
        return False, "Nonce must contain only digits"

    if not 1 <= len(text) <= 19:
        return False, "Nonce must contain 1-19 digits"

    if int(text) <= 0:
        return False, "Nonce must be greater than zero"

    return True, f"nonce={text}"


def check_artifact_url(record: dict) -> tuple[bool, str]:
    url = record.get("artifact_url") or record.get("url")

    if not isinstance(url, str) or not url:
        return False, "Missing artifact URL"

    if not url.startswith("https://github.com/"):
        return False, "Artifact is not a GitHub URL"

    return True, url


def parse_github_url(url: str) -> tuple[str, str, str | None]:
    parts = url.rstrip("/").split("/")

    if len(parts) < 5:
        raise ValueError("Invalid GitHub URL")

    if parts[0] != "https:" or parts[2].lower() != "github.com":
        raise ValueError("Invalid GitHub URL")

    owner = parts[3]
    repo = parts[4].removesuffix(".git")

    branch = None

    if len(parts) >= 7 and parts[5] == "tree":
        branch = parts[6]

    if not owner or not repo:
        raise ValueError("Missing GitHub owner or repository")

    return owner, repo, branch


def github_get(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "technocore-contribution-verifier",
        },
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read().decode("utf-8")

    parsed = json.loads(data)

    if not isinstance(parsed, dict):
        raise ValueError("GitHub returned an invalid response")

    return parsed


def check_github(record: dict) -> tuple[bool, str]:
    url = record.get("artifact_url") or record.get("url")

    if not isinstance(url, str):
        return False, "Missing artifact URL"

    try:
        owner, repo, branch = parse_github_url(url)
    except ValueError as exc:
        return False, str(exc)

    repo_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        repo_data = github_get(repo_url)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        return False, f"GitHub repository check failed: {exc}"

    if "full_name" not in repo_data:
        return False, "GitHub repository not found"

    if branch:
        branch_url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/git/ref/heads/{branch}"
        )

        try:
            branch_data = github_get(branch_url)
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            return False, f"GitHub branch check failed: {exc}"

        if "object" not in branch_data:
            return False, f"Branch not found: {branch}"

        return True, f"{owner}/{repo}; branch={branch}"

    return True, f"{owner}/{repo}"


def check_commit(record: dict) -> tuple[bool, str]:
    commit = record.get("commit")

    if not isinstance(commit, str):
        return False, "Missing commit"

    if not COMMIT_PATTERN.fullmatch(commit):
        return False, "Commit must be a complete 40- or 64-character hash"

    try:
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Git check failed: {exc}"

    if completed.returncode != 0:
        return False, f"Commit not found locally: {commit}"

    return True, f"{commit} exists locally"


def check_proof(record: dict, record_path: Path) -> tuple[bool, str]:
    proof_value = record.get("proof_file")

    if not isinstance(proof_value, str) or not proof_value:
        return False, "Missing proof_file"

    proof_path = Path(proof_value)

    if not proof_path.is_absolute():
        proof_path = (record_path.parent / proof_path).resolve()

    if not proof_path.exists():
        return False, f"Proof file not found: {proof_path}"

    try:
        proof = load_json(proof_path)
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        return False, f"Cannot read proof: {exc}"

    required = {
        "artifact_url",
        "commit",
        "did",
        "schema",
        "signature",
    }

    missing = required - proof.keys()

    if missing:
        return False, "Missing proof fields: " + ", ".join(sorted(missing))

    if proof["schema"] != "technocore-contribution-proof-v1":
        return False, "Unexpected proof schema"

    if proof["did"] != record.get("did"):
        return False, "Proof DID does not match record"

    if proof["artifact_url"] != record.get("artifact_url"):
        return False, "Proof artifact URL does not match record"

    if proof["commit"] != record.get("commit"):
        return False, "Proof commit does not match record"

    if not isinstance(proof["signature"], str) or len(proof["signature"]) < 20:
        return False, "Proof signature is invalid or missing"

    return True, f"Proof verified: {proof_path.name}"


def print_check(name: str, passed: bool, detail: str) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"{status:<5} {name}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a Technocore contribution record and Git proof."
    )

    parser.add_argument(
        "record",
        type=Path,
        help="Path to the contribution JSON record",
    )

    args = parser.parse_args()
    record_path = args.record.resolve()

    try:
        record = load_json(record_path)
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    checks = []

    checks.append(("DID", *check_did(record)))
    checks.append(("Room", *check_room(record)))
    checks.append(("Sequence", *check_seq(record)))
    checks.append(("Nonce", *check_nonce(record)))
    checks.append(("Artifact URL", *check_artifact_url(record)))
    checks.append(("GitHub Artifact", *check_github(record)))
    checks.append(("Git Commit", *check_commit(record)))
    checks.append(("Signed Proof", *check_proof(record, record_path)))

    print("Technocore Contribution Audit")
    print("-" * 32)

    for name, passed, detail in checks:
        print_check(name, passed, detail)

    passed_count = sum(1 for _, passed, _ in checks if passed)
    total = len(checks)

    print("-" * 32)
    print(f"Checks passed: {passed_count}/{total}")

    if passed_count == total:
        print("RESULT: VERIFIED CONTRIBUTION")
        return 0

    print("RESULT: REVIEW REQUIRED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())