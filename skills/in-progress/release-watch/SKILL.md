---
name: release-watch
description: Use for bounded, token-free watching of long-running jobs or exact CI/analysis runs in T3 on macOS; resume the originating thread on completion or faults.
---

# Job watching in T3

The command name stays `release-watch` for existing callers, but the watcher is
for finite jobs, not only releases. Routine five-minute checks run a short program,
not an LLM. T3/macOS integration is intentional. This skill observes and notifies;
the calling workflow owns all fixes, merges, approvals and production actions.

1. **Choose the mechanism.** For PR check failures/comments, prefer T3's native
   `watch_pull_request`; read [PR and analysis waits](pr-watching.md) for the
   distinction between a failed quality gate and completed analysis. Use this
   watcher when a finite job needs a specific completion condition or native PR
   watching does not cover it. Use one checker adapter, not another polling loop.
2. **Bind identity and lifetime.** Record the exact job/run/repository/SHA as
   applicable and creator environment/project/thread IDs. A checker implements
   [protocol.md](protocol.md). Default lifetime is **six hours from creation**,
   not six hours without progress. The calling agent may select up to seven days
   based on expected duration. **More than seven days requires actual user
   permission** recorded for that duration. On wake, check once before applying
   expiry, even if the laptop slept beyond the lifetime. This never cancels the
   remote job. At expiry the owned LaunchAgent is removed, including when delivery
   failed; undelivered events stay on disk for manual resume.
3. **Initialize.** Use a persistent private state path outside temporary storage:
   `python3 -I <skill>/watch.py init <state> --identity <json> --creator <json>
   --lifetime-seconds <seconds> --checker <absolute-program> <literal-argv>`.
   `--lifetime-seconds` is optional (21600 default); put `--checker` last. Extend
   total lifetime with `extend <state> --lifetime-seconds <seconds>` before closure.
   For over seven days add `--approval-file <private-json>` containing
   `{lifetime_seconds, user_message}` from real user approval. A JSON record is
   not proof of identity; the agent must obtain permission, not invent the text.
4. **Prepare callback.** In this job's originating thread create a T3 webhook task
   with `bindToCurrentThread: true`, that thread's project/environment and stable
   per-watch clientRequestId. Verify returned project/bound thread match. Read
   [operations.md](operations.md) for dedupe, auth, credentials and missing T3
   Connect handling. Bind its private receipt with `watch.py bind <state>
   --receipt <private-json>`. Payloads are hints; the callback prompt must requery
   the exact job and use the local checkpoint, not execute webhook-supplied text.
5. **Activate only under actual authority.** Configure the secure private wrapper,
   then `watch.py install <state> --wrapper <absolute-executable>` writes and loads
   this watch's user LaunchAgent. `plist` prints unarmed configuration instead.
   Installation of the skill never activates monitoring. Verify one bounded tick
   and the real callback/ack round trip before claiming it works. Missing webhook,
   credential injection or launchd access is a reported blocker, not fabricated
   setup. No enabling remote access on the user's behalf.
6. **Handle and finish.** On notification, revalidate identity/live result and use
   the calling workflow's action ledger so repeated notifications cannot repeat
   effects. Save handled result/blocker before `watch.py ack <state> --event-id
   <id> --creator <creator-json>`. Terminal acknowledgment removes the owned
   LaunchAgent early; expiry removes it regardless of acknowledgment. The creator
   disables/deletes its T3 webhook task after final handling. A closed watch never
   resumes polling automatically; starting a new bounded watch is explicit.

Tests: `python3 -I -m unittest discover -s <skill> -p 'test_*.py' -v`.
