# PR checks versus exact analysis readiness

For a thread that creates a PR and should resume when Sonar reports a failed
quality gate, use T3's native `watch_pull_request` in that originating thread.
No additional launch job is needed. Existing findings must be handled before
watching; future check changes/comments wake that thread. Keep the watch until
the intended Sonar outcome arrives, not just the first required-check success.
A wake is a notification, never automatic merge or fix permission.

The installed T3 watcher inspected on 2026-11-12 detects newly failed checks from
all reported checks, including optional checks, plus new comments/reviews. It
reports required-check success and can report already-pending optional checks
settling. It does **not** promise a wake when an otherwise-green check merely
adds issue annotations, or when an optional successful analysis first appears
later. Verify behavior on other T3 versions/providers instead of assuming all
analysis events are check failures.

If the desired condition is instead "this exact commit's Sonar analysis is now
ready, regardless of quality-gate conclusion", use a service-specific checker
through this watcher's v1 protocol. Bind PR/repository/full head SHA and trusted
check identity. Missing/queued/running stays pending; a newer rerun supersedes an
older result. Completed analysis can mean ready for inspection even when its
quality gate failed; preserve the actual conclusion separately. Then the creator
queries the analysis service for issues and follows the existing remediation
workflow. A moving PR head requires explicit rebinding, not acceptance of stale
analysis.

Native PR monitoring is the first choice where it covers the requested event.
The generic watcher provides a bounded fallback, not a second PR automation
system. Remediation skill selection, reviewed plans, commit/push permissions and
production approval remain outside monitoring transport.
