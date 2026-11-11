#!/usr/bin/env python3
"""Validate local validation evidence. This is a consistency check, not attestation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)


def source_identity(root, repository, extra_inputs=()):
    root = Path(root).resolve()
    require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root,
            "workspace must be a repository root")
    names = set(os.fsdecode(p) for p in git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0") if p)
    for item in extra_inputs:
        p = root / item
        require(not Path(item).is_absolute() and ".." not in Path(item).parts, "invalid extra input")
        require(p.exists(), "extra input is absent")
        names.update(str(f.relative_to(root)) for f in p.rglob("*") if f.is_file() or f.is_symlink()) if p.is_dir() else names.add(item)
    files = {}
    for name in sorted(names):
        p = root / name
        if p.is_symlink():
            files[name] = {"symlink": os.readlink(p)}
            # Symlinked code/fixtures are inputs too, not merely link text.
            if p.is_file():
                files[name]["sha256"] = digest(p)
            else:
                raise Invalid("directory or broken input symlink: " + name)
        elif p.is_file():
            files[name] = {"sha256": digest(p), "executable": bool(p.stat().st_mode & 0o111)}
        elif not p.exists():
            files[name] = {"missing": True}
        else:
            raise Invalid("unsupported input: " + name)
    return {"repository": repository, "workspace": str(root),
            "head": git(root, "rev-parse", "HEAD").decode().strip(),
            "inputs": files, "digest": canonical(files), "extra_inputs": list(extra_inputs)}


def dependencies_identity(dependencies):
    require(isinstance(dependencies, dict) and isinstance(dependencies.get("artifacts"), list), "dependencies missing")
    actual = []
    for artifact in dependencies["artifacts"]:
        require(isinstance(artifact.get("path"), str) and Path(artifact["path"]).is_absolute(), "dependency needs absolute path")
        actual.append({"path": artifact["path"], "sha256": digest(artifact["path"])})
    return {"source_digest": dependencies.get("source_digest"), "artifacts": actual}


def integer(value):
    return type(value) is int and value >= 0


def validate_plan(plan):
    require(plan.get("schema_version") == 1 and isinstance(plan.get("plan_id"), str) and plan["plan_id"], "invalid plan identity")
    source = plan.get("source", {})
    require(all(source.get(k) for k in ("repository", "workspace", "head", "digest", "inputs")), "source identity missing")
    require(re.fullmatch(r"[0-9a-f]{40,64}", source["head"]) is not None, "full source SHA required")
    require(canonical(source["inputs"]) == source["digest"], "source manifest digest mismatch")
    deps = plan.get("dependencies", {})
    require(deps.get("source_digest") == source["digest"] and isinstance(deps.get("artifacts"), list), "dependency preparation identity missing")
    for a in deps["artifacts"]:
        require(isinstance(a.get("path"), str) and re.fullmatch(r"[0-9a-f]{64}", a.get("sha256", "")), "invalid dependency")
    jobs = plan.get("jobs")
    require(isinstance(jobs, list) and jobs, "plan has no jobs")
    ids = set()
    for job in jobs:
        require(re.fullmatch(r"[A-Za-z0-9_-]+", job.get("id", "")) is not None and job["id"] not in ids, "invalid/duplicate job id")
        ids.add(job["id"])
        require(integer(job.get("test_reruns")), "effective retries required")
        require(isinstance(job.get("argv"), list) and job["argv"] and all(isinstance(a, str) for a in job["argv"]), "approved argv required")
        require(isinstance(job.get("allowed_skips"), list) and all(isinstance(s, str) and "#" in s for s in job["allowed_skips"]), "named skip allowlist required")
        suites = job.get("expected_suites")
        require(isinstance(suites, list) and suites, "expected suites missing")
        require(len({s.get("name") for s in suites}) == len(suites), "duplicate expected suite")
        for suite in suites:
            require(isinstance(suite.get("name"), str) and suite["name"] and integer(suite.get("min_tests")) and suite["min_tests"] > 0, "nonzero expected suite count required")


def parse_report(path):
    raw = Path(path).read_bytes()
    require(len(raw) <= 50_000_000 and b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "unsafe XML report")
    root = ET.fromstring(raw)
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    require(bool(suites), "no suites in XML")
    result = []
    for suite in suites:
        cases = suite.findall("testcase")
        counts = {k: int(suite.attrib.get(k, "0")) for k in ("tests", "failures", "errors", "skipped")}
        require(all(integer(n) for n in counts.values()), "negative XML counts")
        require(counts["tests"] == len(cases), "XML count/testcase mismatch")
        case_ids = [(c.get("classname", suite.get("name", "")), c.get("name", "")) for c in cases]
        require(len(set(case_ids)) == len(cases) and all(name for _, name in case_ids), "duplicate/unnamed testcases")
        skips = [c.get("classname", suite.get("name", "")) + "#" + c.get("name", "") for c in cases if c.find("skipped") is not None]
        require(counts["skipped"] == len(skips), "XML skip count mismatch")
        for tag, key in (("failure", "failures"), ("error", "errors")):
            require(counts[key] == sum(c.find(tag) is not None for c in cases), "XML outcome count mismatch")
        retries = {tag: sum(len(c.findall(tag)) for c in cases) for tag in ("flakyFailure", "rerunFailure", "flakyError", "rerunError")}
        result.append({"name": suite.get("name", ""), **counts, **retries, "skips": skips})
    return result


def artifact(base, record):
    name = record.get("path", "")
    p = (base / name).resolve()
    require(name and p.is_relative_to(base.resolve()) and p.is_file(), "missing/outside evidence artifact")
    require(digest(p) == record.get("sha256"), "evidence hash mismatch")
    return p


def check(plan, receipt, base, check_source=True, allow_retries=False):
    validate_plan(plan)
    require(receipt.get("schema_version") == 1 and receipt.get("kind") == "validation-receipt", "invalid receipt schema")
    require(isinstance(receipt.get("run_id"), str) and receipt["run_id"], "run identity missing")
    require(receipt.get("plan_sha256") == canonical(plan), "plan identity mismatch")
    require(receipt.get("finalized") is True and receipt.get("owned_processes_finished") is True and receipt.get("active_jobs") == [], "unfinished owned execution")
    require(receipt.get("source_before") == plan["source"] == receipt.get("source_after"), "source changed during validation")
    require(receipt.get("dependencies_before") == plan["dependencies"] == receipt.get("dependencies_after"), "dependencies changed/stale")
    if check_source:
        require(source_identity(plan["source"]["workspace"], plan["source"]["repository"], plan["source"].get("extra_inputs", [])) == plan["source"], "current source differs")
        require(dependencies_identity(plan["dependencies"]) == plan["dependencies"], "current dependencies differ")
    jobs = receipt.get("jobs", [])
    require(len(jobs) == len(plan["jobs"]) and len({j.get("id") for j in jobs}) == len(jobs), "job coverage mismatch")
    by_id = {j["id"]: j for j in jobs}
    recovered = False
    for expected in plan["jobs"]:
        job = by_id.get(expected["id"], {})
        require(job.get("state") == "finished" and job.get("owned_processes_finished") is True, "job unfinished")
        require(type(job.get("exit_code")) is int and job["exit_code"] == 0, "command exit failed")
        require(job.get("test_reruns") == expected["test_reruns"], "retry setting differs")
        require(job.get("argv") == expected["argv"], "command differs from plan")
        require(integer(job.get("started_ns")) and integer(job.get("finished_ns")) and job["finished_ns"] >= job["started_ns"], "job timing missing")
        artifact(base, job.get("log", {}))
        suites = []
        reports = job.get("reports", [])
        require(reports, "fresh reports missing")
        paths = set()
        for report in reports:
            require(report.get("fresh") is True and report.get("path") not in paths, "stale/duplicate report")
            paths.add(report["path"])
            require(integer(report.get("mtime_ns")) and job["started_ns"] <= report["mtime_ns"] <= job["finished_ns"], "report outside job interval")
            parsed = parse_report(artifact(base, report))
            require(parsed == report.get("suites"), "parsed outcome mismatch")
            suites.extend(parsed)
        require(len({s["name"] for s in suites}) == len(suites), "duplicate suite evidence")
        for suite in suites:
            require(suite["failures"] == 0 and suite["errors"] == 0, "XML test failures/errors")
            require(set(suite["skips"]) <= set(expected["allowed_skips"]), "unapproved named skip")
            retried = any(suite[k] for k in ("flakyFailure", "rerunFailure", "flakyError", "rerunError"))
            require(not retried or expected["test_reruns"] > 0, "retry evidence with retries disabled")
            recovered |= retried
        actual = {s["name"]: s for s in suites}
        for suite in expected["expected_suites"]:
            require(suite["name"] in actual and actual[suite["name"]]["tests"] - actual[suite["name"]]["skipped"] >= suite["min_tests"], "expected suite missing/insufficient executed tests")
    require(not recovered or allow_retries, "recovered after retries, not first-attempt green")
    return {"accepted": True, "classification": "recovered-after-retries" if recovered else "first-attempt-green"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    identity = commands.add_parser("identity", help="Fingerprint tracked, untracked and explicitly named ignored inputs")
    identity.add_argument("--workspace", type=Path, default=Path.cwd())
    identity.add_argument("--repository", required=True)
    identity.add_argument("--extra-input", action="append", default=[])
    accept = commands.add_parser("check", help="Accept only complete evidence for the exact plan and current source")
    accept.add_argument("--plan", type=Path, required=True)
    accept.add_argument("--receipt", type=Path, required=True)
    accept.add_argument("--allow-retries", action="store_true", help="Accept recovered runs, still labelled recovered")
    args = parser.parse_args()
    try:
        if args.command == "identity":
            result = source_identity(args.workspace, args.repository, args.extra_input)
        else:
            result = check(json.loads(args.plan.read_text()), json.loads(args.receipt.read_text()), args.receipt.parent, allow_retries=args.allow_retries)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError, ET.ParseError, subprocess.SubprocessError):
        print(json.dumps({"accepted": False, "error": "invalid, stale, incomplete or failing evidence"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
