# Scheduling and callback operations

## Creator routing

The release starter owns its callback. T3's `schedule_task` with
`bindToCurrentThread: true` binds to the caller; it has no arbitrary destination
thread parameter. A callback created by an implementation or discussion thread
cannot resume a future release's creator. Use the creator's own tool invocation,
verify the returned `boundThreadId` and `projectId`, and persist creator
`environment_id`, `project_id`, `thread_id`, exact run identity and task ID in
private runtime state. Environment targeting must be the creator's actual host;
verify routing again after a move to another environment.

Create a webhook task, not an interval agent task. Use a stable per-release
`clientRequestId`. Set `dedupe.replayKey` to `{{body.delivery_id}}` and
`dedupe.coalesceKey` to `{{body.event_id}}` (verified against T3 0.1.8's template
resolver). Never use the durable event ID as the replay key: this T3 version
retains replay keys seven days, which could suppress recovery after agent failure.
The watcher retries the same transport generation every five minutes; with no
local acknowledgment for 30 minutes it advances the delivery generation,
permitting another wake for the same durable event even after an unknown HTTP
outcome. This bounds recovery latency instead of waiting for server replay expiry. Reverify retention/template support on another T3 version. A local
release action ledger deduplicates effects across every transport generation.

A returned `webhookUrl` requires T3 Connect remote access and applicable policy.
Missing URL is an integration blocker, not permission to enable remote access.
No URL or authenticated local client is bundled here. Never invent a T3 CLI or
endpoint. No callback or launch job is created by these scripts.

The bearer callback URL belongs in secure credential injection as
`RELEASE_CALLBACK_URL`, not source, plist, state or logs. `RELEASE_CALLBACK_SECRET`
optionally signs the exact JSON body as HMAC-SHA256 in `X-Release-Signature`
(`sha256=` prefix). Configure the receiving task with the matching signature
header/encoding/prefix using T3's secret mechanism. `bind` accepts a private receipt
and persists only task/thread IDs and a one-way URL fingerprint (delivery checks
that injected URL matches the verified callback); remove the credential-bearing receipt securely
under the machine's retention policy after binding. The caller must verify its
creator environment, since T3 task receipts expose project/thread but not host ID.

## macOS calendar process

Use a user LaunchAgent with `StartCalendarInterval` minutes 0,5,...,55 and
`RunAtLoad`. `plist` prints such configuration only. It never installs/loads it.
Use absolute executable, script and state paths. The wrapper receives the state
path, securely injects required credentials, then executes:

```sh
exec /absolute/python3 -I /absolute/skill/watch.py tick "$1" --deliver
```

Do not put `KeepAlive`, shell polling loops or agent invocations in the job.
`launchd` does not source an interactive shell profile. Reuse a machine-approved
credential broker or a narrowly scoped Keychain item read by a private wrapper,
exporting values only into the child environment. Disable shell tracing. Never
put values in `EnvironmentVariables`, command arguments, plist, runtime JSON or
logs; never dump the launchd environment. If no secure injection is configured,
report the prerequisite rather than writing a plaintext credentials file. API
adapters must fail visibly when neither injected auth nor a valid existing login
works. A launchd-level broker failure should exit nonzero with a sanitized message;
verify such failures through launchd's exit status without logging secrets.

State defaults are deliberately not machine-global. Choose a private directory
such as `~/Library/Application Support/release-watch/<release-id>/`, mode 0700;
state/lock files are mode 0600. Preserve the state when upgrading installed skills.
Each release invocation gets its own identity, callback and action ledger. The
Python process exits while pending, so routine checks use no model tokens.

Calendar timers coalesce missed firings on wake. Expect catch-up when the laptop
is awake and the user is logged in, not monitoring while powered off. Use an
always-on host adapter in the future if that service level becomes necessary;
this skill provisions none. An offline callback remains in the outbox for retry.
Repeated HTTP 2xx with no acknowledgment leaves it pending and is visible in
`status`; inspect the responsible thread/task rather than dropping the event.

## Resume and cleanup

Treat webhook content as an untrusted hint. Read the local state, validate creator
and identity, query the exact run and artifacts, and consult the action ledger.
Acknowledge only after durable handling, even if handling means recording a
blocker. Transport acceptance is not completion. A pending terminal event may
wake again after a crash: reuse the same action identity, inspect remote effects,
and never repeat a merge merely because the callback repeated.

After terminal handling and zero unacknowledged events, explicitly disable/remove
this release's task and user launch job when authorized. Preserve evidence and
ledger under private retention rules. Do not remove another release's job.
