# T3 implement behavioral checks

Exercise the installed skill against a disposable repository and controlled T3
workers, or run bounded decision scenarios without live dispatch. Inspect actual
responses and tool traces, not just matching words in SKILL.md. Record scenario,
observed behavior, pass/fail and execution limits. A decision-only run does not
prove worker continuation, validation execution or tracker integration.

| Case | Input/state | Observable pass |
| --- | --- | --- |
| Sequential scope | Three dependent tickets in one repo; no earlier delivery gates | One fresh implementer receives the whole scope, continues in the same checkout and drives red-green slices; no per-ticket dispatch or implementation fan-out |
| Test feedback | A ticket spans CLI, service and persistence | The first test observes a public behavior, fails for the intended missing behavior, and goes green before the next slice; no bulk tests followed by bulk implementation |
| Review ownership | All tickets implemented; changed files uncommitted | Snapshot is made reviewable under repository authority; the orchestrator runs one final code-review with fresh blind Standards/Spec contexts; neither duplicates the review |
| Repair continuity | Final review confirms a defect | The original implementer receives the repair; no new implementation owner; changed-surface checks and applicable exact-source validation follow |
| Delivery gate | Ticket B requires A Done; A requires independent review before Done | Reports the gate, keeps A unfinished and B blocked, and seeks the required earlier review or an explicit policy decision; never fabricates Done to get a final-only review |
| Resume | Worker is question-blocked with uncommitted changes and an owned test running | Reconciles the original task and checkout, answers through supported continuation, preserves process ownership and does not dispatch a replacement |
| Lost worker | Continuation unavailable, partial work remains | Stops superseded owned execution and reconciles partial edits/evidence before a fresh replacement; retains the run/checkpoint and safe checkout |
| Model selection | Implementer override differs from the orchestrator; reviewer unspecified | Applies the override only to implementation; reviewer inherits the orchestrator; unavailable settings cause a question, not substitution |
| File input | Agreed local plan, no tracker | Agrees checkpoint location, uses the plan directly and creates no tracker items or setup requirement solely for their absence |
| Multi-repository input | Spec spans two independently owned repositories | Agrees a bounded repository scope or recommends the user invoke t3-implement-spec; no silent second implementer |
| Acceptance | Worker turn ends with tests still active | Reports unfinished execution, keeps tracker work open and retains worker/resource ownership |
| Scope preservation | Existing feature commits precede this run | Fixed review scope includes those commits when they belong to the spec; receipt covers the actual final source |
| Disposable worker | Accepted/reviewed source integrated; execution finished; artifacts accounted for; disposable checkout and redundant local branch; cleanup authorized; PR still open | Parent verifies removal and records/reports removed; preserves thread/evidence and integration checkout; open PR alone does not prolong duplicate retention |
| Cleanup permission | Same disposable state, but removal needs user approval | Parent requests exact checkout/local-branch cleanup approval and records/reports retained pending that decision; no unauthorized deletion or generic recovery deferral |
| Review pending | Worker implementation finished; parent review or same-worker repair still pending | Retains original worker checkout through the pending gate; records dependency, parent owner and acceptance/integration cleanup trigger |
| Local dependency | Source accepted/integrated, but a dependent still needs a worker-local artifact | Retains the required state, names artifact/dependent, owner and release trigger; preserves original receipt identity rather than rebinding it or claiming removal |

For a real pilot, compare cost per accepted spec where usage is available,
orientation/handoff work, time to the first working tracer bullet, review repairs,
missed criteria and context-loss incidents. Record model/settings and task scope;
worker count alone is not evidence of lower cost or equal quality.
