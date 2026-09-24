"""Explicit public distribution contract for JULIA 0.7.2; no recursive inclusion."""
from pathlib import Path
RELEASE = Path('releases/alpha-007')
LANGUAGES = ('en','ru')
LOCALE_FILES = ('CORE.txt','INFO.md','START_CHAT.txt','REFERENCE.md','SYSTEMS.md','SYSTEMS_53_LEGACY.md','SAVE_GUIDE.md','TESTS.txt','SMOKE_TEST.md')
FILES = ['README.md','LICENSE','.gitignore','RELEASE_STATUS.md','RELEASE_BLOCKS.md','TRANSLATION_REVIEW.md','CHANGELOG.md','SECURITY.md','CONTRIBUTING.md']
FILES += ['.github/CODEOWNERS','.github/PULL_REQUEST_TEMPLATE.md','.github/ISSUE_TEMPLATE/bug.yml','.github/ISSUE_TEMPLATE/config.yml']
FILES += [str(RELEASE / name) for name in ('release.json','VALIDATION.json','SOURCE_PROVENANCE.json')]
FILES += [str(RELEASE / 'locales' / lang / name) for lang in LANGUAGES for name in LOCALE_FILES]
FILES += [str(RELEASE / 'templates' / name) for name in ('STATE_SAVE.json','SELECTIVE_SAVE.json','PLAYER.txt','COMMUNICATION.txt')]
FILES += ['tools/'+name for name in ('release_files.py','build_release.py','verify_release.py',
    'validate_way_direction.py','test_validate_way_direction.py','classify_reward.py','test_classify_reward.py','test_release_integrity.py','test_spike_regressions.py')]
MANIFEST = str(RELEASE/'MANIFEST.json')
NAME = 'P1AY_ALPHA_007_JULIA_V2_CLAUDE_FULL'

VERSION = "0.7.2"
REQUIRED_RULE_IDS = ('COMMUNICATION.RU.001', 'BEHAVIOR.PILLARS.001', 'FOUNDATION.CONTRACT.001', 'REUSE.EXISTING.001', 'ITERATION.CYCLE.001', 'TRUTH.REALITY.001', 'TRUTH.EVIDENCE.001', 'CHOICE.DESIRE_ACTION.001', 'BOUNDARIES.FRIENDSHIP.001', 'SYNC.STATES.001', 'SYNC.AUTHORITY.001', 'CANON.MERGE.001', 'BRAND.EXACT.001', 'COMMANDS.ALIASES.001', 'PPD.PRODUCT_PROOF.001', 'LOAD.RECEIPT.001', 'RELEASE.SCOPE.001')
FILES += ['CORE.md', 'MIGRATION_0_7_2.md', 'canon/CORE_MASTER.json', 'canon/RECONCILIATION.json', 'releases/alpha-007/PRODUCT_MAP_STATUS.json', 'tools/compile_core.py', 'tools/test_canon_072.py']

ARTIFACT_REVISION = 3
FILES += ["releases/alpha-007/MECHANISMS_77.json", "tools/mechanism_registry.py", "tools/test_mechanisms_77.py", "canon/sources/MECHANISMS_77_ORIGINAL_RU.md", "canon/sources/SAVE_DEFINITION_CORRECTION_RU_EN.md", "canon/sources/MECHANISMS_77_APPROVAL_RU.md", "RECOVERY_77.md"]

FILES += ["ARCHITECTURE_FOUNDATION.md"]

# Private Claude transfer layer: canonical pointer, compact computer state and
# the external runtime are explicitly packaged and verified.
FILES += ['CLAUDE.md', 'EXPORT_SCOPE.md', 'pointer/CURRENT_POINTER.json']
FILES += ['compact_state/'+name for name in ('CORE.md','SAVE.json','SYNC.json')]
FILES += ['runtime/'+name for name in (
    '.gitignore','README.md','release.json',
    'docs/ARCHITECTURE.md','docs/OPERATIONS.md','docs/PRIVACY.md',
    'docs/UPGRADE.md','docs/UPGRADE_RU.md',
    'p1ay_sync/__init__.py','p1ay_sync/__main__.py','p1ay_sync/contracts.py',
    'p1ay_sync/engine.py','tests/test_engine.py',
    'schemas/conflict.schema.json','schemas/event.schema.json',
    'schemas/health.schema.json','schemas/migration.schema.json',
    'schemas/receipt.schema.json','schemas/save.schema.json',
    'schemas/selective-save.schema.json','schemas/signed-message.schema.json')]
