# Validation evidence, version 1

A completed worker turn is a result, not acceptance. Before dispatch, agree the validation plan from the ticket's criteria and repository tooling. Use an existing repository runner or CI evidence producer; this protocol requires neither a service nor a particular framework. Backend-specific setup belongs to that repository's test runner, not this document.

## Plan and identity

Keep the approved plan outside fingerprinted inputs, normally in an ignored `.scratch/<feature>/validation/` directory. Generate `source` with:

```sh
python3 -I <implement-spec>/scripts/check-receipt.py identity \
  --workspace /absolute/repository --repository owner/repository
```

The identity records full HEAD, workspace, and a content/mode manifest of tracked and non-ignored untracked inputs, including deleted tracked paths. Add relevant ignored fixtures/configuration with repeated `--extra-input`; symlinked files include target content. Directory/broken input symlinks require an explicit coherent provisioned copy. Secret configuration stays private; the manifest contains hashes, not file contents. Record environment/toolchain/resource configuration separately in the plan. The orchestrator verifies that the selected inputs actually cover the build and test surface.

A plan has these fields (replace placeholders with generated identities/hashes):

```json
{
  "schema_version": 1,
  "plan_id": "feature-validation-1",
  "source": {"repository": "owner/repository", "workspace": "/absolute/repository", "head": "full-sha", "inputs": {}, "digest": "sha256", "extra_inputs": []},
  "dependencies": {"source_digest": "same-source-digest", "artifacts": [{"path": "/absolute/prepared-dependency.jar", "sha256": "sha256"}]},
  "jobs": [{
    "id": "focused-tests",
    "argv": ["repository-test-command", "exact-argument"],
    "test_reruns": 0,
    "expected_suites": [{"name": "fully.qualified.Suite", "min_tests": 1}],
    "allowed_skips": []
  }]
}
```

`dependencies` binds prepared upstream artifacts to the same source digest. Record preparation commands/results and hash the actual consumed artifacts (including test jars, reactor artifacts, and relevant external/toolchain inputs); inspect repository dependency resolution rather than listing just one convenient jar. An empty list is valid only for a self-contained job needing no prepared artifacts. The checker verifies hashes and the binding, not that preparation really happened or that the selected set is exhaustive. Reprepare/replan after source changes; acceptance on another integration workspace needs an explicitly verified input mapping and applicable revalidation, not a workspace-name substitution.

Every planned job names exact argv, expected suite names, minimum **executed, non-skipped** counts, effective retries, and individually allowed `classname#testname` skips. Never permit arbitrary skips by count. Justify allowed names in the plan's accompanying acceptance notes. A skipped required behavior remains unmet even when an unrelated platform skip is allowed.

## Receipt producer

Create a new private directory for every run. Preserve command logs and snapshots without overwriting previous runs. Before each command, preserve/move old reports out of its report location; collect only new reports after the command and its owned processes finish. Record actual exit status even when output is piped or execution is backgrounded. Keep ownership until completion, interruption cleanup, and resource release are established. Jobs still running, detached, question-blocked, interrupted, or unknown are unfinished.

The final receipt contains:

- `schema_version: 1`, `kind: "validation-receipt"`, nonempty `run_id`, and `plan_sha256` (SHA-256 of sorted compact JSON of the approved plan).
- Identical `source_before`, `source_after`, and plan `source`; identical `dependencies_before`, `dependencies_after`, and plan `dependencies`.
- `finalized: true`, `owned_processes_finished: true`, `active_jobs: []`, only after all owned execution ends.
- One `jobs` record for every planned ID: `state: "finished"`, `owned_processes_finished: true`, exact `argv`, integer `exit_code`, effective `test_reruns`, and `started_ns`/`finished_ns` wall-clock timestamps.
- Each job's `log: {"path": "relative/command.log", "sha256": "..."}` and nonempty `reports`. Each report has relative `path`, `sha256`, `fresh: true`, original `mtime_ns` within that job's interval, and `suites` from the checker's `parse_report` function.

Suite records contain `name`, `tests`, `failures`, `errors`, `skipped`, named `skips`, and all four retry-element counts: `flakyFailure`, `rerunFailure`, `flakyError`, `rerunError`. XML is private evidence: extract counts and names, keep properties, diagnostics and raw XML out of summaries. Log producers redact secrets before publishing immutable logs; never dump the environment.

## Acceptance

```sh
python3 -I <implement-spec>/scripts/check-receipt.py check \
  --plan /private/run/plan.json --receipt /private/run/receipt.json
```

Exit 0 means mechanically accepted; exit 1 rejects incomplete, stale, mismatched or failing evidence. The checker rehashes the current workspace, dependencies, logs and XML, verifies plan/job/suite coverage, validates parsed counts, and treats command exits and XML outcomes as separate requirements. It rejects unfinished jobs, absent/zero expected suites, unapproved named skips, and retry-bearing evidence by default. Explicit `--allow-retries` can accept a justified recovered run, always classified `recovered-after-retries`, never first-attempt green. Record that policy decision rather than hiding a flake behind Maven's success exit.

The orchestrator checks acceptance-criterion coverage and evidence relevance after the script succeeds. Hashes and shape checks are consistency controls, not signatures: a producer can forge a coherent receipt, omit relevant inputs, or lie about freshness/process ownership. This script cannot guarantee model obedience, semantic correctness, or an unforgeable execution history. A stronger repository may bind it to trusted CI without making self-hosted infrastructure a prerequisite here. No completion hook or provider-specific stop veto is required.
