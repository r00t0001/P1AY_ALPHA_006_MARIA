# User upgrade and migration

1. Record installed CORE version, SAVE schema and SHA-256 of the original bytes. Make a private backup and verify restore before changing files.
2. Resolve the owner through the trusted registry. Conflicting IDs, unknown aliases, unknown schema and unverifiable sources stay on HOLD. Never infer identity from a filename.
3. Install the candidate runtime/CORE in a separate directory. Verify the distribution manifest. Older public V5 remains a historical release; a new candidate must have its own version/hash and validation record.
4. Run `migrate OWNER original.json envelope.json`. The migration accepts recognized SAVE_02/03/04 and verified identity. It preserves the entire original object, including unknown fields, permissions, PAUSED, handshakes, quests and history. It records source schema and normalized content hash. It does not turn missing fields into invented state or silently reclassify rewards.
5. The output is P1AY_MIGRATION_ENVELOPE_01 / STAGED_NOT_APPLIED, not a fictional complete SAVE_04. Keep original raw bytes alongside it. An old shape that fails the full current contract requires explicit field mapping and review; no blanket semantic 02→04 converter is supplied.
6. Register source evidence; review differences; propose, approve and apply a valid full SAVE event. A valid existing SAVE is preserved as a bootstrap before updates. Never overwrite the input file.
7. Export the signed event. Enroll each device deliberately; apply on the peer with its own validation/approval and return its receipt. Until then display LOCAL_ONLY_OR_PEER_PENDING.
8. Record the installed release hash and resulting content version for each device. Publishing a new repository cannot update previously downloaded CORE files automatically.

Rollback: retain old installation and immutable versions. Restore a verified DB backup to a new path using `restore backup.sqlite --sha256 HASH`; compare heads, conflicts and receipts, then explicitly select it. Do not overwrite a live database or delete newer history. PAUSED remains PAUSED throughout.
