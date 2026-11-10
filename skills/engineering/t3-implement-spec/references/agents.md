# Resolve agents

Use current thread configuration and live T3 capabilities to resolve the
orchestrator's provider **instance**, model, and applicable settings. Unspecified
roles inherit that selection, not a destination project's defaults. Apply explicit
overrides only to their named roles, translating supported settings when changing
providers. Ask about ambiguous/unavailable selections rather than silently
substituting an agent. Pass the resolved selection on cross-project launches;
permission-mode limits apply independently.
