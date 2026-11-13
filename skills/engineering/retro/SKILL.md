---
name: retro
description: "Conduct a retrospective on a coding session."
disable-model-invocation: true
---

Suggest improvements to the coding agent's **environment** that would improve
future runs. This is a proposal-only retrospective: investigate and discuss;
implementation starts only after the user approves it.

## Steps

1. Call the Skill tool with `writing-for-agents` for the writing style guide.

2. Read the specified session's **primary sources**, or the current session when
   none is specified. Preserve the user's focus and the assessed time/message
   boundary. Locate corrections, failed attempts and their consequences, and the
   instructions and tools governing them. Read relevant original exchanges and
   artifacts, not just the final success summary. Report source-access gaps and
   limit conclusions accordingly.

3. Investigate candidates using the categories below as prompts, not a quota.
   For each candidate, check the relevant existing capability and the narrowest
   evidence that could disprove its need. Inspect pending work when the evidence
   suggests overlap or version skew, rather than searching every open change.
   Distinguish **missing** guidance, **unreached** guidance (a navigation problem),
   and clear guidance that was **ignored** (noncompliance). Repeating an existing
   instruction is not automatically a remedy. Keep only candidates with an
   observed consequence and a credible benefit; frequency alone is not harm.

4. Present the surviving recommendations in severity order. Make the **first
   substantive response decision-ready**: for every recommendation, supply the
   information below, with depth proportional to the intervention. These are
   required facts, not mandatory repeated headings. If none survive, say that no
   worthwhile change is supported and briefly name the decisive checks.

   - **Pain and cause:** what happened, why it matters, and the session evidence.
     Separate established cause from inference; include the check and result
     supporting the proposal.
   - **Targets and mechanism:** name the owning skill/tool/repository and exact
     source files verified to exist. Label new files as **proposed** and unresolved
     locations as **unknown**. Explain in plain language what would happen
     differently. If the mechanism is not yet defensible, propose a bounded
     investigation rather than a tool with invented precision.
   - **Scope and route:** justify personal, shared/team, or external ownership by
     effects, not source visibility or ignore status. Name the implementation
     boundary and needed authority. Account for rollout and coordination costs,
     including the user's preference for personal experimentation, without making
     that preference a ban on shared tools. Where relevant, recommend starting
     and eventual scope and the evidence that would justify promotion. A personal
     pilot can be a route to shared adoption; some shared risks need a shared
     boundary immediately.
   - **Trade-off and proof:** explain complexity and maintenance burden, compare
     the simplest credible alternative (including doing nothing), and state how
     to verify that the intervention addresses the observed pain. A complicated
     tool must earn its cost over a smaller change.

## Investigation prompts

- **Navigation:** slow discovery, hidden dependencies, or instructions never
  reached. Consider a pointer from a file the agent already reads.
- **Automated checks:** mistakes a machine could catch. Read the relevant build
  check commands and their wiring first: an existing but unwired or broken check
  may be the finding. Missing guardrails are candidates when tied to observed
  risk, not automatic recommendations to add CI.
- **Coding standards:** mistakes the reviewer missed. Prefer a deterministic check
  for mechanical patterns; reserve reviewer standards for judgement calls. Select
  the cheapest effective enforcement at the justified scope, rather than assuming
  every check belongs in shared lint, hooks, or CI.
- **Steering files:** large `AGENTS.md`/`CLAUDE.md` files, misplaced standards, and
  no-op instructions. Consider disclosure, relocation, or deletion where the
  session supports it.
- **Tool economy:** expensive calls with little useful return; consider a simpler
  call or existing tool before proposing another one.
- **Information access:** crucial information the agent could not reach. Consider
  appropriately scoped logs or read-only access, accounting for permissions.

## Reference

### Implementation and review

The implementation agent explores, writes, and debugs under high **context
pressure**. Review usually has a narrower diff-focused task. Put judgement-call
coding standards where the reviewer will read them, rather than loading every
standard into every implementation session.

### Instruction homes

- `CLAUDE.md`/`AGENTS.md`: always-loaded steering, used sparingly, usually for
  **navigation pointers**.
- Existing standards such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`: reviewer
  guidance. Prefer existing homes; disclose large references behind pointers.
- Docs: on-demand reference, reached through an appropriate pointer.
- Skills: model-discovered reference or user-invoked workflows, following
  `writing-for-agents`.

When refining this skill, exercise [behavioral checks](checks.md) against actual
responses; a written checklist alone is not a behavioral result.
