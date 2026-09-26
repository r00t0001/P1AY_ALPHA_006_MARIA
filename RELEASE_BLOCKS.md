# Release boundaries · 0.7.2

## Current open gates
1. Complete named 77-mechanism source map: not recovered. Do not claim enumeration completeness.
2. Sync-runtime source (runtime/p1ay_sync/) is bundled for audit and unit-tested (19 tests), but its live installation on the owner's Mac, real-device round-trip receipts and independent security review remain external gates. Bundled code is not the same as an installed, running service.
3. Exact-hash live model behavior and independent technical/translation review: pending.
4. PPD command semantics: not recovered; must not invent them.

Critical privacy, identity, data-loss or irreversible-migration defects block the affected component until FIX or explicit SCOPE_OUT plus independent review. This candidate makes no new independent acceptance claim. It is not a permission to bypass a downstream release gate.

Historical RB-001 selective-transfer fix is retained as code/rules, not newly independently certified for these bytes. No private PLAYER migration runs when using the text protocol.
