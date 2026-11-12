---
"mattpocock-skills": minor
---

Broaden release-watch to finite T3/macOS jobs and exact analysis readiness. Make it
model-reachable for calling skills. Replace the no-progress timeout with a six-hour
default lifetime, caller-selected extensions up to seven days and explicit user
permission beyond that. Check once after wake before expiry, retain undelivered
events, and remove only the owned LaunchAgent on expiry or terminal acknowledgment.
Document native PR watching as the first choice for check failures/comments.
