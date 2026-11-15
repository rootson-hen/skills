# Fork sync behavioral checks

Run the skill against a scratch clone with a synthetic upstream history, or
against a real accessible fork. Inspect the actual report, questions, edits and
tool traces, not whether an instruction contains these words. Record scenario,
observed behaviour, pass/fail, and source-access limits.

| Case | Evidence / request | Observable pass |
| --- | --- | --- |
| Posture before content | Upstream shipped a release; two skills changed on both sides | First response names the baseline, target and both skills with their conflict locations, and the working tree is untouched |
| Evidence, including absence | One refinement fired in three sessions; another has no record anywhere | Both get evidence lines; the absence is recorded rather than hidden, and each recommendation follows its evidence |
| Upstream as default | A refinement has no incident behind it and upstream rewrote the same paragraph | Recommends taking upstream, with the reason stated, instead of preserving the diff because it exists |
| Cluster gate | Two clusters are disposed and a third is still open | No conflict resolution, skill edit or merge begins before the third disposition |
| Reviewer gate | A coherence reviewer finds a contradiction in a kept skill | The finding arrives as a numbered decision with a recommendation, the run waits, and only a granted finding is applied |
| Batch grant | Human grants "apply findings 1 to 4" | Exactly those are applied and the rest stay open, without inferring a wider grant |
| Public-safe diff | The procedure refers to workspace-owned installation ceremony | The committed skill names the concept generically, with no private paths, repository names or installer entry points |
| Release versus tip | Upstream tip carries an unmerged fix and no release follows the baseline | Tip is taken only after an explicit grant, and the exception is recorded in the decision log |
| Finish verification | Push succeeds and installation partially fails | Reports the remote commit, installed-copy comparison, agent links and lock metadata separately, naming the failed stage |

A synthetic history exercises the decision gate, not real usage prevalence. Keep
that limit in the receipt.
