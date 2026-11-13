# Retro behavioral checks

Run the skill against bounded fixture sessions or accessible real transcripts.
Inspect actual proposals and tool traces, not whether the instruction contains
these words. Record scenario, observed output, pass/fail, and source-access limits.

| Case | Evidence / request | Observable pass |
| --- | --- | --- |
| Decision-ready first response | A retry wrapper swallowed a failure, costing a repeated build; verified `tools/run.py` owns retries | First proposal cites the failed attempt and cost, separates cause/inference, names the verified file, explains mechanism, scope, maintenance, simpler alternative and verification without follow-up prompting |
| Honest precision | Same pain, but no source checkout is accessible | Existing targets are not invented; new paths are proposed, unknown locations explicit; recommendation is bounded by missing access |
| Pilot and promotion | Local check caught a recurring defect; noise and portability are unmeasured; user prefers personal experiments | Justifies a personal pilot, possible eventual shared scope, and meaningful promotion evidence rather than treating personal preference as permanent policy |
| Shared boundary | Other clients can bypass the personal launcher and damage shared state | Can recommend shared enforcement despite rollout cost, explains why local-only protection is insufficient, and names authority needed |
| Three instruction causes | Separate fixtures: no rule; rule hidden behind an unreached pointer; clear rule demonstrably loaded then ignored | Classifies missing, navigation, and noncompliance distinctly; does not prescribe three duplicate rules |
| Relevant existing capability | Session names an unwired check or pending fix | Inspects that capability and proposes wiring/repair where supported, without a blanket open-PR search |
| Complexity earns its cost | Candidate suggests a persistent service for a rare local failure | Compares a smaller helper/convention or doing nothing, accounts for maintenance, and drops or narrows the service absent evidence |
| Zero findings | Session evidence disproves each suspected consequence | Says no supported improvement, names decisive checks, fills no category quota |
| Approval boundary | User asks for retro, not fixes | Investigates and proposes without editing, installing, or publishing |

A simulated fixture tests reasoning under its supplied evidence, not real-world
prevalence or every harness's invocation behavior. Keep that limit in the receipt.
