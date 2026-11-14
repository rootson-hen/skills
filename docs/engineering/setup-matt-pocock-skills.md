## What it does

`setup-matt-pocock-skills` answers three questions about one repo: where issues live, what the triage labels are called, and where the domain docs sit. It records the answers as markdown files under `docs/agents/`, preserving existing custom paths reached through repository configuration pointers. Tracker setup also establishes where orchestration checkpoints persist, without moving active ledgers. When [commit](https://aihero.dev/skills-commit) is installed, it also offers optional setup of repository-specific commit-message requirements.

Those files are the only thing that varies between repos. The skills themselves are identical everywhere; tracker consumers follow the repository instruction files' pointers and do what the configured workflow says. That is why the set is not tied to GitHub, and why no skill file ever needs editing to point it somewhere else. Invoking it with "link the skills to a custom issue tracker" works with anything you can connect to programmatically, with zero changes to the skills.

It is a prompt-driven skill, not a deterministic script. It reads your `git remote`, your existing `CLAUDE.md`, your existing `GLOSSARY.md`, and any existing `docs/agents/commit-messages.md`, proposes what it found, and waits for you to confirm before writing anything.

## When to reach for it

You invoke this by typing `/setup-matt-pocock-skills`; the [agent](https://www.aihero.dev/ai-coding-dictionary/agent) won't reach for it on its own. Its metadata marks it non-invokable on purpose, so no other skill can fire it for you.

Reach for it once per repo, before the first use of any other engineering skill. If [triage](https://aihero.dev/skills-triage), [to-spec](https://aihero.dev/skills-to-spec), [to-tickets](https://aihero.dev/skills-to-tickets) or [wayfinder](https://aihero.dev/skills-wayfinder) start guessing where your issues go, or apply labels your tracker doesn't have, this repo has not been set up yet. You can run it in a repo halfway through a project. The skill reads what is already there, so no earlier work is lost.

## Prerequisites

It writes into the repo you run it in:

| It writes | Where |
| --- | --- |
| Tracker workflow and checkpoint policy | Existing pointed-to tracker doc, or `docs/agents/issue-tracker.md` for new setup |
| `domain.md` | `docs/agents/` |
| `triage-labels.md` | `docs/agents/`, only when the `triage` skill is installed |
| `commit-messages.md` | `docs/agents/`, only when `commit` is installed and you confirm a repository-specific policy |
| An `## Agent skills` block | whichever of `CLAUDE.md` / `AGENTS.md` already exists |

You commit all of it as markdown. There is no user-level or global mode. The config lives in the repo, so every repo gets its own copy.

## The three decisions

The core setup still covers these three decisions. It leads each section with the recommended answer, and skips whatever exploration already settled. Most runs are two confirmations and done.

| Decision | What it proposes | When it asks |
| --- | --- | --- |
| **Issue tracker** | the one matching your `git remote` | always, because this is the one real choice |
| **Triage labels** | keep the five canonical names (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) | only if the `triage` skill is installed |
| **Domain docs** | single-context: one `GLOSSARY.md` plus `docs/adr/` at the root | only if it spots monorepo signals, and then it offers a multi-context `GLOSSARY-MAP.md` |

For the domain-docs decision, a repo predating the `GLOSSARY` names may still carry the legacy `CONTEXT.md` / `CONTEXT-MAP.md`. When setup finds one, it offers to `git mv` it to its `GLOSSARY` name and rewrite those names in `docs/agents/domain.md`, so the layout it records matches the files that exist.

The tracker options:

| Option | Where issues live | Needs |
| --- | --- | --- |
| **GitHub** | the repo's GitHub Issues | the `gh` CLI |
| **GitLab** | the repo's GitLab Issues | the `glab` CLI |
| **Local markdown** | files under `.scratch/<feature>/` in this repo | nothing, not even a remote |
| **Other** | wherever you say | one paragraph from you describing the workflow |

The first three ship as templates in the skill and work out of the box. Local markdown is a first-class option, not a fallback: a solo project with no remote is fully supported. Issue trackers are alternatives, not duplicate authorities. A deliberate local orchestration-checkpoint exception can coexist with remote issues; it does not create a local copy of their requirements or lifecycle.

"Other" is a full option too. It is how Jira, Linear, Azure DevOps and Beads all work. You describe the workflow, the skill records your prose in `docs/agents/issue-tracker.md`, and the downstream skills follow the prose. Users have already built this: a Jira-over-[MCP](https://www.aihero.dev/ai-coding-dictionary/mcp) variant, a Gitea CLI shaped like `gh`, a hand-built local dashboard.

## Orchestration persistence

Tracker setup includes a policy for one mutable **checkpoint** per orchestration
run, with one active orchestrator per Spec. It records persistence and access
conventions, not T3 worker IDs or run-specific state.

- Local Markdown normally stores `orchestration.md` beside the Spec.
- Jira and GitHub normally use one editable checkpoint comment on the Spec;
  GitLab uses an editable note when supported.
- Explicit local exceptions are preserved. If available tooling, permissions,
  capacity, or visibility make a backend unsuitable, agree one fallback before
  dispatch instead of silently creating a second authority.

Setup presents the policy with its draft. It does not create test tracker records
or relocate active ledgers. Older repositories without a checkpoint policy still
work: the orchestration skill prefers suitable persistence in their configured
tracker after checking capabilities. Existing runs resume in their existing home.

## Optional commit-message policy

When `commit` is installed, setup offers to help create `docs/agents/commit-messages.md`:

- An existing policy is reused unless you confirm a change.
- A new policy records only explicit repository or user requirements, and is written only after you confirm the requirements and draft. Jira references, time values, and workflow transitions are never invented.
- If the default Conventional Commit format is enough, the file stays absent.

`commit` reads the file directly, so setup adds no policy pointer to `AGENTS.md` or `CLAUDE.md`.

## Common questions

**Do I have to use GitHub?**

No. GitHub, GitLab and local markdown under `.scratch/` all ship as ready-made templates, and anything else works through the "other" path. This is the most-repeated question, in roughly these words: *"hard locked to github"*, *"can I use GitLab / Jira"*, *"what about Azure DevOps"*. The answer is always the same: setup chooses the tracker, not the skill.

**Do I need to re-run it after updating the skills?**

The direct answer after v1.1 was yes. The skill's own closing message is softer. It tells you to re-run only to switch trackers or start over. Both are defensible. The seed templates change between versions, so a `docs/agents/issue-tracker.md` from an older release can go out of date against the skills that now read it. If a downstream skill does something different from what the docs describe, re-run setup. It is cheap.

**It wrote to `CLAUDE.md`, but I'm on Codex.**

This is a known gap, and still open. The file-selection rule is "edit `CLAUDE.md` if it exists, else `AGENTS.md`". It checks which file exists, not which [harness](https://www.aihero.dev/ai-coding-dictionary/harness) is running. In a repo with a `CLAUDE.md` left over from Claude Code, the skill writes its `## Agent skills` block to a file Codex never reads. Users have two workarounds: move the block to `AGENTS.md` by hand, or keep `AGENTS.md` canonical and make `CLAUDE.md` a one-line pointer at it. If neither file exists, the skill asks you which to create instead of picking one. This has confused people who expected it to decide.

**It didn't create my triage labels.**

On GitHub and GitLab it now does: when the label step ran, setup creates each configured label the tracker lacks (`gh label create` / `glab label create`). `docs/agents/triage-labels.md` remains a *mapping* that tells `/triage` which strings in your tracker correspond to the five canonical roles, so if your tracker already uses the canonical names the mapping is an identity table and there is nothing to create. One gap remains: this skill does not create [wayfinder](https://aihero.dev/skills-wayfinder)'s `wayfinder:map` and `wayfinder:<type>` labels, and `gh issue create --label <missing>` fails instead of creating the label. Create them by hand before the first wayfinder run on a GitHub repo.

**Can I configure the other skills' behaviour here ([grilling](https://www.aihero.dev/ai-coding-dictionary/grilling) cadence, question format, tone)?**

Not general preferences. Its core setup covers the tracker and orchestration persistence, labels, and doc layout; when `commit` is installed, it can also record an optional repository commit-message policy. There have been direct requests to make it the home for per-user preferences, and the standing answer is that skills stay opinionated: *"Config is death."* Preferences such as cadence and tone belong in your `CLAUDE.md` as plain instructions, which every skill already reads.

**Can I keep the config in `~/.claude` instead of committing it to every repo?**

Not today. A user who runs the skills across many repos has an open request for this, but no user-level mode exists. Every repo carries its own `docs/agents/`.

**Isn't it strange to have a skill that configures the other skills?**

One long-standing complaint says yes, in these words: *"having a skill to set up the other skill does not feel right to me: that means the LLM is configuring its own skills."* The trade-off is real. Without a setup step, every skill that touches issues would need its own copy of the tracker instructions. The output is markdown you can read and edit, and that limits the risk. You can read every file it wrote and change it by hand. Make day-to-day changes that way, not with another run.

## It's working if

- The tracker doc exists at its configured path, along with `docs/agents/domain.md` and `triage-labels.md` if `triage` is installed.
- An `## Agent skills` section appears in the instruction file your harness actually reads, with a one-line summary pointing at each of those files.
- The tracker it proposed matches the remote you really use, and the label strings match labels that really exist in your tracker.
- Afterwards, `/to-tickets` publishes without asking you where issues live, and `/triage` applies labels rather than inventing them.
- Orchestration persistence follows the configured backend or explicit exception, while active ledgers remain untouched by setup.
- Any new commit-message policy contains only requirements you confirmed; choosing the default leaves an absent `docs/agents/commit-messages.md` uncreated.
- Nothing in the skill files themselves changed. If setup edited a `SKILL.md`, something went wrong.

## Where it fits

`setup-matt-pocock-skills` is the **run-once setup** for the engineering flow, the precondition everything else assumes rather than a step in the chain. Its neighbours are its readers: [triage](https://aihero.dev/skills-triage), which applies the label vocabulary written here; [to-spec](https://aihero.dev/skills-to-spec) and [to-tickets](https://aihero.dev/skills-to-tickets), which publish into the tracker named here; and [wayfinder](https://aihero.dev/skills-wayfinder), which reads the "Wayfinding operations" section of the same tracker file to learn how to store maps and child [tickets](https://www.aihero.dev/ai-coding-dictionary/ticket). [domain-modeling](https://aihero.dev/skills-domain-modeling) later fills in the domain-doc layout that setup records. It creates `GLOSSARY.md` and ADRs only when you resolve a term or decision, so a repo with no domain docs after setup is normal. For which skill to reach for next, [ask-matt](https://aihero.dev/skills-ask-matt) routes the whole set.
