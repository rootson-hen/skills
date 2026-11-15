## What it does

`fork-sync` brings a customized fork of these skills up to date with upstream without losing the refinements that earned their place. Its defining constraint is that it does not merge by default: upstream's text is the starting position for every skill, and a personal change survives only where real use of the skill shows the incident it prevents.

The run produces a posture report, one evidence line per skill changed on both sides, and a **disposition** for each: keep the fork's line, take upstream's, adapt it, or retire the refinement.

## When to reach for it

You invoke this by typing `/fork-sync`, and the agent won't reach for it on its own. Run it when upstream publishes a release you want to adopt, or when you want to know how far the fork has drifted.

- For what one working session taught about the agent's environment, use [retro](https://aihero.dev/skills-retro).
- For a review of your own work since a fixed point, use [code-review](https://aihero.dev/skills-code-review). `fork-sync` compares two histories with each other instead.

## Prerequisites

A checkout of the fork with an `upstream` remote, the coordinating workspace's install ceremony, and access to the transcripts or thread records where the skills actually ran. Without that usage record the evidence stage degrades to "no usage found", which pushes every recommendation toward upstream.

## Posture before merge

The first response is a report, not a merge: which release was adopted last, which release is the target, what changed upstream and in the fork, and exactly where the two edits collide. Reading it tells you the size of the decision in front of you before any file moves.

The upstream target is the newest release by default. An unreleased tip is available, because a fork sometimes needs a fix that has not shipped, but taking it is an explicit exception rather than the normal route.

## Dispositions, not diffs

A **disposition** is a sentence a human says about one cluster of changes, and the run does not continue past an open one. The evidence stage exists to make that sentence well informed: what the refinement was protecting, whether it ever fired, and what happened when it did.

| Disposition | Meaning |
| --- | --- |
| Keep | Real use shows the incident the fork's line prevents, and upstream still lacks that protection |
| Take upstream | No use, indifferent use, or upstream now covers the same need more simply |
| Adapt | The purpose survives, but the text has to change to fit what upstream now does |
| Retire | The problem has gone, or a different skill now owns it |

The same rule governs the coherence pass after the merge. A fresh reviewer reads each contested skill whole, and every finding comes back as a numbered decision with a recommendation. The reviewer reports; you dispose. Nothing is applied until you say so, individually or as an explicit batch.

## Common questions

**Does it always take upstream's version?**

No. Upstream is the default, not a rule. A refinement stays when the record shows the incident it prevented and that incident still exists. A fork that refuses every upstream change is as unmanaged as one that accepts every diff.

**What happens to a skill with no transcripts at all?**

It becomes a "no usage found" line, and the recommendation leans upstream. You can still keep the line on a stated reason, which is a different decision from keeping it because the code already differs.

**Will it resolve conflicts and tell me afterwards what it did?**

No. Conflicts are resolved in the merge stage, after every cluster has a disposition. Findings that arrive afterwards are decisions too, and the run waits for them.

**Can I grant a batch of fixes at once?**

Yes. Name the findings, such as "apply 1 to 4", and exactly those are applied. A general "looks good" is read as approval of the decisions already on the table, not as standing permission for whatever a later reviewer finds.

## It's working if

- The first report names every skill changed on both sides before any file changes.
- Each contested skill carries an evidence line, including the ones where no usage was found.
- Reviewer findings arrive as numbered decisions, and the run is still waiting rather than reporting completed fixes.
- The decision log says why each refinement stayed, adapted, or went, in terms of use rather than diff size.

## Where it fits

`fork-sync` is **periodic maintenance** for the fork itself, not a step in a build. It owns how the decisions are reached; [FORK.md](https://github.com/rootson-hen/skills/blob/personal/FORK.md) owns the git ceremony, the release policy and the decision log it appends to.

It pairs with [retro](https://aihero.dev/skills-retro), which proposes changes to a session's environment, where `fork-sync` decides which already-made changes survive an upstream import. [ask-matt](https://aihero.dev/skills-ask-matt) maps the rest of the set.
