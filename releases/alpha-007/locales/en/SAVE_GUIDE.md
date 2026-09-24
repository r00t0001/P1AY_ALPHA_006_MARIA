# SAVE ownership and migration

Public templates contain no real owner or personal facts. Create a separate private folder for each verified owner. Never import another owner's level, history or tasks. The local project roster is evidence about participants, not a replacement for SAVE files received from those participants.

At the first SAVE, the user chooses `LOCAL ONLY`, `PRIVATE LINK SYNC`, `SELECTIVE SAVE LINK`, or `NO SYNC / LATER`. For link sync, the user uploads the SAVE to their own private storage and shares a link. The common index stores the link, claimed owner, schema/provenance/permission state, conflicts, merge state, and feedback state; it does not publish the complete personal SAVE. A link is `RECEIVED_LINK`, not a verified import. Independently verify owner, access, schema, and provenance before merge. Silence does not enable synchronization.

STATE_SAVE.json is P1AY_SAVE_04, the current empty state template (not legacy). SELECTIVE_SAVE.json is P1AY_SELECTIVE_SAVE_02 for selected transfer. Keep owner, source revision, recipient, purpose, scope, terms, duration, consent, owner confirmation, provenance, transfer evidence and revocation explicit. `NOT_GRANTED` or `NOT_CONFIRMED` means no transfer is authorized. Empty selection exports nothing. A full recovery backup stays private. Passwords and raw secrets are excluded.

Before importing: preserve original bytes and SHA-256; verify owner independently of filename; check schema/core version, revision/date, PAUSED, visibility and permissions; validate task structure; deduplicate event IDs and causal groups; preserve conflicts for review. A matching identifier is not authentication. Never treat a template as a received profile.

SAVE_03 → SAVE_04: retain task IDs and history, change way_direction.tasks to background_tasks, require three owned tasks per selected direction, and use main_task_ids plus open_main_slots = 3. MAIN spans both directions when all slots are filled. DONE/WAITING/IN_REVIEW/CANCELLED do not occupy MAIN. Preserve every DONE result, evidence, award and dedup key. Never silently activate proposed/waiting tasks. If the old file has only three tasks total, record a migration gap; do not invent three more. Run onboarding when quest_model_version is not WAY_6BG_3MAIN_001. Imported PAUSED requires a separate explicit resume after import.

Validation: python3 tools/validate_way_direction.py path/to/STATE_SAVE.json. This checks structure, not identity, consent or truth. Keep received originals immutable; create a new reviewed version. Status is PREPARED_NOT_SENT until actual write/verification or transfer, and each transition needs its own receipt. Do not upload personal SAVE files to GitHub.


## LEGACY

Pre-PROGRESSION_TIER_CLASSIFIER_001 levels are preserved as LEGACY: not comparable with the current scale and not verified by the current classifier. Display LEGACY beside each such level in profiles, statistics and SAVE exports. Preserve original numbers, events, scale and provenance separately from current verified points; never add the scales together. Do not erase history or automatically convert it into current awards. Reclassification requires a separate explicit procedure with the full gate and duplicate checks; event_id and dedup_group identify events but do not replace evidence or an independent verifier. An event failing the gate remains UNCLASSIFIED_REWARD_CANDIDATE without current points. Awards already claimed under the new scale without the full gate are verification conflicts, not automatically LEGACY or VERIFIED.
