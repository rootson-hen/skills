---
name: fork-sync
description: "Bring this fork up to date with upstream, deciding every skill change with you."
disable-model-invocation: true
---

# Fork sync

This fork carries personal refinements on `personal` while upstream keeps moving.
Adopting an upstream release is a **decision procedure**, not a merge: upstream's
text is the default for every skill, and a refinement survives only where real use
shows the incident it prevents.

`FORK.md` at the repository root owns the branch policy, the git ceremony, and the
refinement decision log. This skill owns how the decisions are reached. The unit of
decision is a **disposition**: keep the fork's line, take upstream, adapt, or
retire, stated explicitly for each cluster before any content changes.

## 1. Posture

Read `FORK.md`, then fetch and measure the gap without touching `personal`. Report:

- the baseline release recorded by the last merge, and the upstream target: the
  newest release by default, an unreleased tip only on an explicit grant;
- commit and file counts, and every skill upstream changed;
- every skill the fork changed since the baseline, and which of those upstream
  also changed;
- the conflict hunks for each both-sides-changed skill, previewed rather than
  merged.

Completion: every both-sides-changed skill is named with its conflict locations
and the last recorded decision for it. No working-tree change yet.

## 2. Evidence

For every both-sides-changed skill, establish what the fork's refinement was for
and whether real use needed it. Mine the places the skills actually ran: session
transcripts, agent thread records, and installed-skill history. When the sources
span more than one store, dispatch a background subagent with a fresh context
window per store and collect its report.

Each skill gets one evidence line: the incident or purpose behind the refinement,
whether it fired, what happened when it did, and what upstream's change does to
that purpose. "No usage found" is a result, recorded as such.

Completion: every both-sides-changed skill has an evidence line or an explicit
no-usage finding.

## 3. Decision interview

Call the Skill tool with "grilling". Work in clusters, one per skill or per shared
purpose, in rounds. Each cluster presents the fork's line, upstream's change, the
evidence, a recommendation with its reason, and what carrying the refinement
would cost.

The recommendation follows the evidence: take upstream when use was absent or
indifferent; keep or adapt the fork's line when use shows the incident it
prevented. Upstream's simpler text wins ties.

Dispositions are the human's. Do not resolve conflicts, edit skill content, or
start the merge while any cluster is undecided.

Completion: every cluster carries an explicit disposition.

## 4. Merge and validate

Apply the dispositions with `FORK.md`'s ceremony and its release-versus-tip
policy. Where a skill is kept or adapted, verify that its references, examples,
and sibling dependencies still resolve after the merge.

Run the repository's validation for what changed: `claude plugin validate .
--strict` after manifest edits, `git diff --check`, and the tests belonging to
touched skills.

Completion: the staged diff matches the dispositions, and validation passes or
its exceptions are named.

## 5. Coherence pass

Dispatch one fresh reviewer per both-sides-changed skill, each with a fresh
context window and the whole final skill rather than the diff. The brief: does it
read as one coherent skill, and do its docs page, README entry, router mention,
references, and callers still agree with it?

Every finding returns to the human as a numbered decision with a recommendation,
and waits there. Apply what is granted, one by one or as an explicit batch. The
reviewer reports; the human disposes.

Completion: every finding carries a disposition.

## 6. Finish

Commit the merge as `FORK.md` describes, with one decision-log entry per cluster
recording the evidence and the reason. Push `personal`.

Installation is separate and belongs to the coordinating workspace's `AGENTS.md`:
reinstall this fork's collection for every configured agent, then verify the
installed copies against `personal`, the agent links against the canonical copy,
and the installer lock's source and branch metadata.

Completion: the remote branch contains the merge commit, installed content matches
it, and any failed or skipped stage is reported.
