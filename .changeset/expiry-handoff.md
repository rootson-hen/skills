---
"mattpocock-skills": patch
---

Make expiration a final notification handoff to the originating T3 agent before
local schedule cleanup, including credential-wrapper fault paths. Require expiry
callback instructions to inspect the job, choose continuation, a replacement
bounded watch or user input from task context, and retire only the old resources.
Test creator-bound delivery before cleanup and retain offline events durably.
