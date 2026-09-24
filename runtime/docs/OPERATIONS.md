# Operations

All commands require `--db /private/path/state.sqlite` and optionally `--device COMPUTER|PHONE`. They do not send data or change sharing.

- `init identity.json`: register local identity and generate private local signing key.
- `source OWNER reference file`: pin a local evidence file hash; changed bytes need a new reference.
- `bootstrap OWNER reference save.json`: preserve an already authoritative snapshot; exact normalized payload must match registered source.
- `propose OWNER save.json --output event.json`: validate and stage a local signed event; does not apply it.
- `receive event.json`: authenticate a registered peer and stage/reject/conflict the event.
- `approve EVENT --evidence reference`, then `apply EVENT`: evidence-bound state transition. Approval does not bypass stale-base or continuity checks.
- `export-outbox OWNER directory`: immutable retry-safe filenames; export does not mark delivery complete.
- `enroll OWNER PEER key-file`: explicit trusted enrollment. Never paste keys into Sheet, chat, public repository or logs.
- `ack receipt.json`: verify peer signature, owner, event and exact applied content version. Local/self receipts do not count as peer confirmation.
- `observe-panel NAME rows.json`: observe all ID-bearing data rows, including previously seen/open conflicts. Pass complete data rows without title/header; partial ranges must never be represented as complete snapshots. Changes/deletions enter append-only observation history.
- `resolve CONFLICT --evidence reference`: preserve history and record resolution; rebasing is a separate event.
- `backup new-path.sqlite`: SQLite backup API, integrity check and SHA-256. Never copy an active DB without its WAL using ordinary file copy.
- `restore backup.sqlite --sha256 HASH`: verified restore to a nonexistent destination.

Drive transport remains an authenticated connector operation. Upload only to an owner-only folder; fetch bytes and compare before accepting a remote backup. Sheet projection contains health only, not full SAVE or keys. Its timestamp is projection time, not peer application time.

An observer can run repeatedly. It must record start/end/errors, reread all relevant rows, and never suppress a changed old conflict. Agent heartbeat is still the scheduler; this release does not install a persistent server or claim a strict hourly SLA. Keep health/error notifications separate from canonical PLAYER to avoid backup loops.
