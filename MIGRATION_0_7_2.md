# Updating to 0.7.2 / Обновление

1. Preserve your existing CORE and personal SAVE as a private backup. Do not delete history.
2. Select one language and actually read the new CORE.txt. Treat its version as declared until hashes are checked.
3. Load your own selected SAVE. Keep owner, permissions, PAUSED, conflicts, completed results, existing awards and task state. Never replace it with an empty template.
4. WAY_6BG_3MAIN_001 stays unchanged. A valid profile using it needs no repeated onboarding or new awards. A PAUSED profile remains paused; migration is not resume.
5. Conflict between a newer local master and this package: record both sources; do not silently downgrade.
6. Verify with compile_core.py --check and verify_release.py; record the final ZIP hash for a live test.

На компьютере общий источник сборки — canon/CORE_MASTER.json. Корневой CORE.md и два CORE.txt — генерируемые представления. Это не замена private/PLAYER.md и не установщик внешнего sync-runtime. Телефонная запись про дружбу передаётся отдельным приватным пакетом для принятия в личную память, а не в биографии получателей релиза.

## R2 / mechanics77
This patch restores an omitted approved registry, not a new profile schema. The version remains 0.7.2, artifact_revision is 3, and the build has a new SHA-256. Use the R3 architecture-foundation archive for further distribution instead of treating the earlier 0.7.2 bytes as equivalent. No old personal state is overwritten and no score, task or consent is reset. Do not silently downgrade a newer local master.
