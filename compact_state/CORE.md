# P1AY — компактная рабочая память

Основные объекты: CORE.md (порядок), SAVE.json (зафиксированные решения и этапы Yes), SYNC.json (проверка), действующий персональный SAVE через private/sync/CANONICAL_SAVE_POINTERS.json. Персональная authority — private/PLAYER.md и обязательный load_player_context; этот проектный SAVE её не заменяет.

Журнал подтверждений хранится в private/sync_runtime/state.sqlite вместе с прежним транзакционным движком. Готовые проекции предназначены только для приватной папки P1AY_SYNC, никогда для общего LINE. Полная переписка не дублируется в каждый SAVE и не перечитывается без причины.

После значимого этапа: `PYTHONPATH=sync-runtime python3 -m p1ay_sync.workspace --config private/compact_sync/p1ay.json save`. Для передачи через уже установленный Drive: та же команда с `once`. Сначала сохраняется локальная версия, затем отдельно проверяется сервер.

Первый Yes на «развернуть?» записывается командой `yes --stage 1` с точным текстом; второй по тому же предмету — `yes --stage 2`, статус confirmed twice. До этого `offer` с уникальным ID/темой. Смена темы, неоднозначность или NO: `cancel`. Прямое поручение сохраняется через `record`, без выдуманных Yes. Подробности команд: sync-runtime/docs/COMPACT_WORKSPACE.md.

Важные записи сохраняются отдельно от автоматического изменения канонического профиля, permissions, PAUSED и scores. Для переноса в канон действуют существующие identity/source/review gates. Фоновый код не читает все чаты: исполнитель вызывает команды сохранения по фактическому ответу пользователя.

## CURRENT CORE ROUTE · 0.7.2 R3

Сначала читать `CURRENT_POINTER.json` (Drive ID
`11srcpREyWiX5EOH4TuAYymccZ5QxNz-N`). Он указывает на единственный
редактируемый источник общего протокола: `CORE_MASTER.json` (Drive ID
`19CJy5qku8dptUuKFBndcaLn3CyZoMYd7`). Текущий R3 source SHA-256:
`d6ea14fb76a8371f22afe0c7f3cce94c50000b3c941c02b8d90f1b94fba7c868`.
Человекочитаемый R3 CORE — генерируемая проекция (Drive ID
`1mHOLweYlHJBtX8Az-mgAIgKA86FgV7Lc`). При запросе «все CORE canons»
проверить в актуальном source утверждённый порядок 19 пунктов основы.
При запросе механик проверить 77 исходных названий и определений.
Этот компактный файл — маршрут и квитанция, а не полный список правил.

`private/core/P1AY_CORE.md` — локальная историческая копия, которая пока не
сверена побайтно с R3. Её исторический раздел нельзя использовать
как полный текущий canon. Если pointer или source недоступен, сообщить об этом
и не выдавать сокращённую копию за все действующие правила.

build_id: `0.7.2-r3-architecture-foundation`; artifact_revision: `3`;
mechanism_registry_count: `77`. Требование 77/77 нельзя отменять из-за
неудачного поиска. CORE, PLAYER, SAVE и история сохраняют разные области
authority; данные с телефона являются delta до подтверждённого merge.

## PREVIOUS RECEIPT · R2 / 77 · 2026-09-24

- artifact_revision: `2`
- build_id: `0.7.2-r2-mechanics77`
- mechanism_registry_count: `77`
- CORE_MASTER_sha256: `8c1c7e555d93c272a71220710d78566e33eccdf2c60f8b93a04de686493cf35b`
- CURRENT_POINTER_sha256: `549b1704ba3056ded21f57055d03fbadb254126f9a08258e8bf5e6ebd540a8ac`
- required_rules: `COMMUNICATION.RU.001`, `BOUNDARIES.FRIENDSHIP.001`

Compact CORE remains a pointer / operational memory and does not duplicate the full 77 definitions.

## CANONICAL RECEIPT · R3 / ARCHITECTURE FOUNDATION + 77 · 2026-09-25

- artifact_revision: `3`
- build_id: `0.7.2-r3-architecture-foundation`
- mechanism_registry_count: `77`
- CORE_MASTER_sha256: `d6ea14fb76a8371f22afe0c7f3cce94c50000b3c941c02b8d90f1b94fba7c868`
- CURRENT_POINTER_sha256: `341e0bdf691c918957c2649a70de76dddfd34870bddf09c6785eddc4accf056e`
- architecture_foundation: `OWNER_APPROVED_CANONICAL`
- rule_ids_renamed: `false`

### ОСНОВА АРХИТЕКТУРЫ P1AY · НОРМАТИВНЫЙ ПОРЯДОК

01. FOUNDATION.CONTRACT.001
02. TRUTH.REALITY.001
03. TRUTH.EVIDENCE.001
04. BEHAVIOR.PILLARS.001
05. COMMUNICATION.RU.001
06. SHORT FIRST NORMALIZED
07. BOUNDARIES.FRIENDSHIP.001
08. REUSE.EXISTING.001
09. CHOICE.DESIRE_ACTION.001
10. ITERATION.CYCLE.001
11. SYNC.AUTHORITY.001
12. SYNC.STATES.001
13. LINK-BASED SAVE SYNC
14. CANON.MERGE.001
15. PPD.PRODUCT_PROOF.001
16. LOAD.RECEIPT.001
17. RELEASE.SCOPE.001
18. COMMANDS.ALIASES.001
19. BRAND.EXACT.001
