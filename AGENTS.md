# AGENTS.md

## CLI/GUI semantic parity

When a feature is exposed through both the CLI and the GUI, both interfaces must share the same application semantics, domain rules, and structured results.

Neither interface may independently reimplement, reinterpret, or alter the behavior of the other. Differences are allowed only in presentation and interaction, not in the meaning of the data or in the outcome of the operation.

If a change affects the behavior of a feature available in both CLI and GUI, its impact on both interfaces must be reviewed and verified in the same change.
