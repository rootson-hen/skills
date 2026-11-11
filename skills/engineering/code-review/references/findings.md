# Discovery, adjudication, verification

## Blind discovery

Run Standards and Spec in independent, fresh contexts, in parallel. Give each the pinned source/base/scope, its original requirements or standards, and accessible repository instructions. Keep previous findings, dispositions, repair reports, and the orchestrator's preferred conclusion out of both briefs and their supplied context. State that discovery is blind and that reviewers should perform it directly without spawning reviewers. If a governing document contains earlier dispositions, provision a requirements-only source while preserving the real requirements and applicable instructions.

Each reviewer assigns **review-local IDs**, such as `S1` or `P1`; they are not stable identities across rounds. Save the original reports under `.scratch/<feature>/reviews/<round>/standards.md` and `spec.md`, preserving each axis and its citations. Aggregate side by side as the skill specifies.

## Reconcile after discovery

The orchestrator owns `.scratch/<feature>/reviews/findings.json`. Reconcile only after the independent reports arrive. This findings ledger is a decision artifact, separate from any orchestration resume checkpoint; point to it from that checkpoint rather than copying it.

Use this compact shape:

```json
{
  "schema_version": 1,
  "source": {"repository": "owner/repository", "base": "full-base-sha", "head": "full-head-sha", "scope": "whole-feature", "inputs_digest": "optional-uncommitted-input-digest"},
  "claims": [{
    "id": "C1",
    "claim": "Stable, concrete behavioral or standards claim",
    "source": {"repository": "owner/repository", "base": "full-base-sha", "head": "full-head-sha", "scope": "whole-feature", "inputs_digest": "optional-uncommitted-input-digest"},
    "observations": [{"axis": "Spec", "round": "round-1", "local_id": "P1", "source": {"head": "original-reviewed-sha"}, "report": {"path": "round-1/spec.md", "sha256": "report-hash"}}],
    "disposition": "accepted",
    "reason": "Evidence and authority for this decision",
    "repair": null,
    "verification": null,
    "duplicate_of": null
  }]
}
```

Preserve stable claims and original observations, including original reviewed identities, while recording their current applicability in `source`. A new observation of the same claim links to it; a distinct claim can link with `duplicate_of`. A repeated ID or similar wording is not proof of semantic equivalence. Compare concrete requirement, failure mechanism, inputs, consequence and changed source before deciding. Preserve disagreements and separate axes, even when they concern the same code.

| Disposition | Meaning |
| --- | --- |
| `required` | An in-scope correction or unresolved acceptance blocker. Must be fixed or explicitly adjudicated before acceptance. |
| `optional` | A useful improvement, not a completion blocker; record why. |
| `accepted` | Deliberate behavior, rebutted claim or accepted tradeoff, with evidence/authority. |
| `deferred` | Out-of-scope work with reason and owner/follow-up where needed. Required criteria can be deferred only through an explicit scope decision. |
| `fixed` | Repair pointer plus passing verification against the current source. |

A smell is a judgment call, not automatically required. A duplicate of an accepted claim is not automatically a fresh blocker. New concrete evidence or changed invariants can reopen it as `required`, with the reason recorded. Never close a required criterion merely to make the ledger pass.

## Targeted verification

Give a repair verifier the specific claim, repair diff and affected surface. Explicitly label the task **verification, not blind discovery**. It may see the prior finding and fix; it confirms the repaired behavior, regressions and impact rather than pretending to be unbiased discovery. Store its result as `verification: {"source": <current identity>, "outcome": "passed", "evidence": {"path": "round-1/verification.md", "sha256": "..."}}` and a nonempty `repair` pointer.

Recheck the changed surface and its impact after repairs, refresh relevant validation receipts, and re-pin applicable claims with a reason when source changes. Use another full blind review when changed invariants or substantive reconciliation justify new discovery; record that scope decision. Cosmetic churn alone is not a reason for an indefinite broad-review loop.

```sh
python3 -I <code-review>/scripts/check-findings.py \
  --ledger .scratch/<feature>/reviews/findings.json --source /private/current-review-identity.json
```

Exit 0 checks shape, current-source identity, evidence-file hashes, duplicate links, and absence of open `required` claims. Exit 1 reports a structural/open/stale ledger. The script does not decide semantic equivalence, whether a disposition is justified, whether discovery was genuinely blind, or whether the evidence proves the claim. Those remain the orchestrator's responsibility.
