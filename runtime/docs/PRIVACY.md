# Privacy and release boundary

The distributable allowlist consists of Python sources, synthetic tests/examples, JSON schemas, documentation and release metadata. Exclude private/, *.sqlite*, *.db*, actual SAVE, account email, provider file IDs, local source paths, credentials and device secrets. A `.gitignore` is defense in depth; release construction uses an explicit allowlist and scans every included text file.

Local SQLite and exported outbox/backup files are mode 0600. They are not application-encrypted; filesystem/account access remains a trust boundary. HMAC authenticates a registered device, not the truth of player assertions. Registered-source fingerprints establish byte provenance, not semantic correctness. Explicit review still owns canonical decisions.

No public sharing or third-party sending occurs automatically. Selective SAVE consent/recipient/scope remain separate from full private synchronization. Never replace a selection with full PLAYER. Google Sheet health can disclose IDs and activity timing, so keep the current panel owner-only.

Do not claim multi-user authorization isolation from this local administrator-controlled CLI. A future service requires a separate authenticated account/authorization layer and key management.
