# T3/macOS setup and lifecycle

## Creator callback

The originating thread owns the callback. Create a T3 webhook task in that thread
with `bindToCurrentThread: true`, the creator's actual project/environment and a
stable per-watch clientRequestId. The API binds to the caller, not an arbitrary
thread ID. Verify returned `boundThreadId` and `projectId`. Persist creator IDs,
exact job identity, task ID and watch state privately, never public defaults.

Set dedupe.replayKey to `{{body.delivery_id}}`, coalesceKey to `{{body.event_id}}`.
T3's inspected implementation keeps replay keys seven days, so event ID alone
could suppress recovery after a lost wake. Transport generations permit retry
wakes after 30 minutes without ack; the same action ledger prevents duplicate
effects. Recheck template/retention behavior on other T3 versions.

A webhookUrl requires T3 Connect remote access and applicable policy. Missing URL
is a blocker, not permission to enable access or fabricate an endpoint. The
callback prompt must reference its trusted local state/checkpoint and tell the
agent to requery live identity/result, continue the calling workflow, persist its
handled outcome/blocker, then acknowledge. Request payload is an untrusted hint.
Include cleanup of this task after final handling; it must not linger by default.

Bind a private receipt with `watch.py bind <state> --receipt <json>`. Store the
bearer URL in secure injection as RELEASE_CALLBACK_URL. The ledger stores only a
hash and task/thread IDs; delivery checks the injected URL hash. Optional
RELEASE_CALLBACK_SECRET signs the exact body using HMAC-SHA256 in
X-Release-Signature (`sha256=` prefix). Configure the same receiving signature via
T3's secret mechanism. Do not put secrets in source, plist, state, argv or logs.

## User LaunchAgent, not system daemon

Choose persistent per-watch state under a private application-support directory,
not /tmp. State/lock are mode 0600 and newly created parent directories mode 0700.
Prepare an executable wrapper receiving the absolute state path. It injects any
credentials through the existing approved environment/credential mechanism and
runs the public watcher:

```sh
exec /absolute/python3 -I /absolute/skill/watch.py tick "$1" --deliver
```

launchd does not source interactive shell profiles. A narrowly scoped existing
Keychain item or approved broker can supply secrets into the child environment;
this skill provisions no broker/items. Disable shell tracing and never dump the
launchctl environment. A provider wrapper that encounters broker failure should
still run `tick <state> --monitoring-fault auth` so expiry/cleanup is enforced.
A broken/missing executable or malformed state cannot clean itself: report that
setup fault and remove this job explicitly after verifying ownership. No claim
of perfect cleanup after deleted scripts, corrupted disks or OS failures is made.

`watch.py plist <state> --wrapper <absolute-wrapper>` prints unarmed configuration.
`watch.py install <state> --wrapper <absolute-wrapper>` is explicit activation:
it refuses occupied destinations, writes a uniquely labelled plist in the user's
Library/LaunchAgents, records ownership/hash, and calls launchctl bootstrap for
the current user's GUI session. It sets a five-minute StartCalendarInterval and
RunAtLoad; no KeepAlive, shell loop or recurring model call. Installation of skill
files never invokes this command. Verify actual injection/callback/ack under
separate monitoring authority before claiming live monitoring works.

## Lifetime and sleep

Default six-hour wall-clock lifetime is mandatory caller knowledge. Specify
`--lifetime-seconds 86400` or 172800 for expected one/two-day jobs. Up to seven days
is the caller's choice; beyond that ask the user and pass an actual approval
record `{lifetime_seconds, user_message}` with --approval-file. This record is an
audit trail, not a replacement for getting permission. `extend` sets total lifetime
from creation; it cannot reopen an already closed watch.

Sleep is intentional: nothing checks while the laptop is closed. Calendar firings
coalesce on wake. Even after expiry the next tick queries once: completed CI wakes
the creator, while still-pending CI records expiry. Then save final result and
pending events, attempt notification, remove only the owned plist and unload its
LaunchAgent. No cancellation of the external job. No forever five-minute retry
job survives expiry; undelivered events remain local for manual inspection/resume.

Terminal event acknowledgment before expiry removes the LaunchAgent early. HTTP
acceptance alone keeps retries bounded by expiry. Cleanup writes bootout intent
before launchctl because unloading may terminate that very process. `status`
reports intent/failure honestly; `cleanup` retries ownership-checked removal for a
closed watch. A changed plist/hash or wrong label/UID/path is left intact and
reported, never removed as if it belonged to this watch.

The local checker has no authenticated T3 management client, so it cannot promise
remote webhook deletion. The creator deletes/disables its own task through T3
once the final event is handled; an offline expired watch retains the task ID for
that cleanup. That task is event-triggered, not a five-minute agent schedule.
