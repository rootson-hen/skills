#!/usr/bin/env python3
"""Check review-ledger structure and closure, not claim equivalence or reviewer independence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def reference(base, ref):
    path = (base / ref["path"]).resolve()
    require(path.is_relative_to(base.resolve()) and path.is_file(), "missing/outside evidence reference")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == ref["sha256"], "evidence changed")


def check(ledger, source, base):
    require(ledger.get("schema_version") == 1 and ledger.get("source") == source and bool(source), "ledger source mismatch")
    require(all(isinstance(source.get(k), str) and source[k] for k in ("repository", "scope")) and
            all(re.fullmatch(r"[0-9a-f]{40,64}", source.get(k, "")) for k in ("base", "head")), "full review identity required")
    claims = ledger.get("claims")
    require(isinstance(claims, list), "claims missing")
    ids = {c.get("id") for c in claims}
    require(len(ids) == len(claims) and all(isinstance(i, str) and i for i in ids), "claim IDs invalid")
    for claim in claims:
        require(isinstance(claim.get("claim"), str) and claim["claim"] and claim.get("source") == source, "claim/source missing")
        state = claim.get("disposition")
        require(state in {"required", "optional", "accepted", "deferred", "fixed"}, "disposition invalid")
        require(isinstance(claim.get("reason"), str) and claim["reason"], "disposition reason missing")
        observations = claim.get("observations")
        require(isinstance(observations, list) and observations, "observations missing")
        for observation in observations:
            require(observation.get("axis") in {"Standards", "Spec"} and all(observation.get(k) for k in ("round", "local_id", "source")), "observation identity missing")
            reference(base, observation["report"])
        duplicate = claim.get("duplicate_of")
        require(not duplicate or duplicate in ids and duplicate != claim["id"], "invalid duplicate link")
        require(state != "required", "open required finding")
        if state == "fixed":
            require(bool(claim.get("repair")), "repair missing")
            verification = claim.get("verification", {})
            require(verification.get("source") == source and verification.get("outcome") == "passed", "verification missing/stale")
            reference(base, verification["evidence"])
    # Links preserve observations; cycles cannot stand in for an adjudication.
    links = {c["id"]: c.get("duplicate_of") for c in claims}
    for start in links:
        visited = set()
        while start:
            require(start not in visited, "duplicate cycle")
            visited.add(start)
            start = links[start]
    return {"accepted": True, "claims": len(claims)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path, help="Expected current review identity JSON")
    args = parser.parse_args()
    try:
        print(json.dumps(check(json.loads(args.ledger.read_text()), json.loads(args.source.read_text()), args.ledger.parent)))
        return 0
    except (ValueError, OSError, KeyError, TypeError):
        print(json.dumps({"accepted": False, "error": "invalid, open or stale review ledger"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
