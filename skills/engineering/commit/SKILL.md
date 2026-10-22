---
name: commit
description: Create a local Git commit.
---

1. Inspect the current branch and changes, including the staged diff. Include only changes belonging to the requested work.

2. Read `docs/agents/commit-messages.md` relative to the repository root if it exists. Follow its message format and other applicable repository requirements.

3. If the file is absent, use a concise Conventional Commit title in imperative mood. Add a body only when useful. Omit issue references, worklogs, and transitions unless explicitly required.

4. Commit on the current branch with normal Git hooks enabled. Correct validation failures rather than bypassing them. If requirements conflict or remain unclear, ask the user.

5. Report the commit hash and message. Do not push.
