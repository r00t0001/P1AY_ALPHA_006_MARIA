# Architecture

`verified local source → signed event → durable inbox → validation → evidence-bound approval → transactional apply → receipt/outbox → transport → peer apply → signed peer receipt`

SQLite owns the operational journal. Google Sheet is a projection/observation panel; editing it never writes canonical SAVE directly. The existing PLAYER registry remains identity authority. Bootstrap preserves an explicitly selected canonical SAVE exactly, including legacy gaps; it does not claim to merge a newer registry into that SAVE.

Tables: identities and enrolled peers; immutable source fingerprints; events with stable IDs; immutable content-addressed versions and heads; approvals bound to event hashes; conflicts and append-only conflict revisions; receipts; outbox; run receipts; full panel row fingerprints and change history. Writes use BEGIN IMMEDIATE and synchronous FULL. A version, head update and local receipt/outbox entry commit together. A process crash before COMMIT leaves the prior head intact.

Repeat event ID + same signed body returns its existing status. Same ID + different body fails. Stale base becomes a conflict, including when the head advances between stage and apply. Conflict resolution records evidence but never applies a stale event; produce a reviewed event based on the current head.

History/list records and fields cannot silently disappear. PAUSED cannot be resumed by this generic merge path. A separate, reviewed resume migration is required. Other meaningful changes require a local approval with a registered evidence reference. CLI access is an administrative trust boundary: registering a source is an explicit trust decision, not proof that every assertion in it is true.

Device authentication uses per-device HMAC-SHA256 keys pinned during explicit enrollment. Keys are private runtime data. This is a small trusted deployment protocol, not multi-tenant/public-key infrastructure: an administrator possessing peer keys can impersonate them. Loss/theft requires explicit key rotation and re-enrollment, not silent replacement. External clients must implement the same canonical JSON serialization; interoperable cross-language signing is not claimed by the Python-only fixture test.

Health separates local version, staged/rejected events, unresolved engine conflicts, pending delivery and matching peer APPLIED evidence. Panel conflicts are observations and are reported separately from engine merge conflicts. A receipt confirms one event/version at a time; it does not establish permanent equality or peer liveness.
