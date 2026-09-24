# P1▶Y · ALPHA_007 / JULIA · 0.7.2 · R3 / 77

Portable text protocol · MIT · reviewed-source reconciliation candidate.

## Start / Начало
Choose one language: `releases/alpha-007/locales/ru/` or `releases/alpha-007/locales/en/`.
Attach `CORE.txt` and `START_CHAT.txt` to your AI conversation. For an update, keep your own SAVE and its permissions, history, pending conflicts and PAUSED state. Do not import the empty template over an existing profile.

Для русской версии можно использовать единый `CORE.md` в корне: это побайтовая генерируемая копия русского CORE.txt, а не отдельный master. Установка программы или автоматической синхронизации не требуется и не заявляется.

## One authoring source
`canon/CORE_MASTER.json` is the only authoring source for both languages and the root CORE view. Edit it, run `python3 tools/compile_core.py`, inspect the changes, then rebuild. Do not edit generated CORE copies independently.

```
python3 tools/compile_core.py --check
python3 tools/verify_release.py
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/build_release.py --output ./dist/0.7.2-reviewed
```

The builder checks an explicit file allowlist, generated-source parity, required rule IDs/text, all 77 source-bound names/definitions, privacy markers, JSON defaults, version metadata and the final extracted ZIP. It does not certify model behavior or evidence truth.

## Included
Restored communication canon; human choice and boundaries; retained WAY and scoring contracts; default-safe empty SAVE templates; complete approved 77-item map and separate historical 53-system reference; deterministic compiler, verifier, regression tests and source-disposition register.

## Not included / not certified
The existing external SQLite/Drive synchronization runtime, private profiles and conversations are not distributed. All 77 original grouped definitions are now included; English descriptions are translated for this recovery, with explicit provenance. This is not certification of 77 implemented external services. PPD's retained text contract is included, not a measured product result. New exact-hash live model tests and independent reviews are still required. The user's computer master is not silently overwritten by extracting this package.

See [release status](RELEASE_STATUS.md), [changes](CHANGELOG.md), [migration](MIGRATION_0_7_2.md), and [reconciliation](canon/RECONCILIATION.json).

## 0.7.2 R3 / восстановление 77
The artifact revision distinguishes this build from the earlier 0.7.2 ZIP. The earlier bytes remain historical, not silently identical. See [recovery evidence and limits](RECOVERY_77.md). The complete registry is included in both CORE editions, not only referenced by a number.
