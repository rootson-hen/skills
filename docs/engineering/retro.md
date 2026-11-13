## What it does

`retro` looks back over a coding [session](https://www.aihero.dev/ai-coding-dictionary/session) and proposes improvements to the agent's **[environment](https://www.aihero.dev/ai-coding-dictionary/environment)**. Its first substantive response is **decision-ready**: you can see the pain, evidence, exact targets, mechanism, scope, cost, and verification before deciding whether to proceed.

It proposes rather than implements. Categories guide investigation, not the number of findings, and no worthwhile change is a valid result. A longer answer is not the goal; enough grounded detail to make a decision is.

## When to reach for it

You invoke this by typing `/retro`, and the agent won't reach for it on its own. Use it after a session with costly mistakes, slow discovery, or repeated user corrections. It reads the current session by default, or the history you specify, and stays in place rather than routing to another workspace.

- For a verdict on the code produced, use [code-review](https://aihero.dev/skills-code-review).
- For structural improvements discovered from code rather than session history, use [improve-codebase-architecture](https://aihero.dev/skills-improve-codebase-architecture).

## Decision-ready proposals

A recommendation explains what went wrong and why the proposed intervention earns its cost. Existing target files are checked, new files are labelled proposed, and unknown locations remain explicit. An uncertain mechanism calls for bounded investigation, not invented precision.

Scope follows the effects, not whether a file is public or ignored:

| Scope | What the recommendation explains |
| --- | --- |
| Personal | Why local tooling is sufficient and what it costs to maintain |
| Shared or team | Why the shared boundary is needed despite coordination and rollout cost |
| External | Which tool or provider owns the fix and what authority the route needs |
| Personal pilot, possibly shared later | Why to start small and what evidence would justify promotion |

Personal experimentation can be cheaper and easier to reverse, but it cannot protect shared state from clients that bypass it. The recommendation makes that trade-off visible rather than silently imposing either scope.

## Evidence before more instructions

The workflow checks the relevant existing capability before proposing another one. A broken or unwired check may need repair, not replacement. It investigates pending work when the session suggests overlap, without searching every open change.

Instruction failures have different remedies:

- **Missing:** guidance may need a home.
- **Unreached:** navigation may need a better pointer.
- **Ignored:** clear guidance was available but not followed; another copy is not automatically a fix.

Mechanical mistakes favor an **[automated check](https://www.aihero.dev/ai-coding-dictionary/automated-check)** at the cheapest effective scope. Judgement-call standards belong where the reviewer reads them, rather than adding every rule to always-loaded steering.

## Common questions

**Why does the first answer need more than a list of ideas?**

A plausible idea can still solve the wrong pain or cost more than a small alternative. The proposal names the evidence, affected files, mechanism and maintenance burden so you can challenge it immediately. It also explains how to tell whether the change helps.

**Will it invent generic advice to fill the categories?**

It should present only candidates supported by a consequence in the session and a check that holds up. Repetition alone is not harm. An empty result with the decisive checks is complete, not a failed retrospective.

**Does it build the proposed check or change team tooling immediately?**

No. Implementation needs approval, including the scope and route. A personal workflow preference does not silently become team CI, and a justified shared fix is not ruled out merely because personal tools are easier to introduce.

**Does this audit all the checks from earlier retros?**

No. It evaluates the specified session and relevant capabilities, not the lifetime health of every rule or hook. A check that becomes noisy still needs evidence and a separate pruning decision.

**My session is long. Run it now, or start fresh?**

Either works if the relevant original exchanges and artifacts remain accessible. A fresh run needs source pointers and the assessment boundary; a success summary alone is insufficient. Missing access should limit the conclusions rather than invite speculation.

## It's working if

- You can decide on a recommendation without asking which files, whose tooling, or why it is needed.
- A complex proposal compares a simpler alternative and explains its maintenance cost.
- Personal pilots can have justified promotion criteria, while shared risks can earn shared enforcement.
- An existing rule or check is recognized before another one is proposed.
- Unsupported candidates disappear, even when that leaves no recommendations.

## Where it fits

`retro` closes the main chain after implementation and [code-review](https://aihero.dev/skills-code-review), but also works as a standalone look back at a specified session. [writing-for-agents](https://aihero.dev/skills-writing-for-agents) supplies the writing discipline for the steering it proposes. [ask-matt](https://aihero.dev/skills-ask-matt) maps the broader set.
