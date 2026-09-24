"""Verify the exact public allowlist, locale parity, privacy boundary and manifest."""
import hashlib
import json
import re
from pathlib import Path
from release_files import FILES, MANIFEST, RELEASE, LOCALE_FILES, LANGUAGES, VERSION, REQUIRED_RULE_IDS
from compile_core import compile_core
from mechanism_registry import validate_registry, registry_view
from validate_way_direction import validate_way_direction
class VerificationError(ValueError):
    """A hard validation failure; never removed by python -O."""
    pass

ROOT = Path(__file__).resolve().parents[1]

def verify(root=ROOT, require_manifest=None):
    if require_manifest is None:
        require_manifest = (root / MANIFEST).is_file()
    for name in FILES:
        p = root / name
        if not (p.is_file() and (not p.is_symlink())):
            raise VerificationError(f'Missing or symlink: {name}')
        data = p.read_bytes()
        text = data.decode('utf-8')
        if not len(data) < 5000000:
            raise VerificationError(f'Oversized: {name}')
        forbidden = ('BEGIN ' + 'PRIVATE KEY', 'BEGIN ' + 'OPENSSH PRIVATE KEY')
        if name != 'compact_state/SAVE.json':
            forbidden += ('/' + 'Users/', '/var/' + 'folders/')
        if not not any((v in text for v in forbidden)):
            raise VerificationError(f'Private marker: {name}')
        if not not re.search('(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}', text):
            raise VerificationError(f'Credential marker: {name}')
        removed_owner = 'player' + 'number0001'
        public_email = 'happy.tv.int' + '@gmail.com'
        if not removed_owner not in text:
            raise VerificationError(f'Removed GitHub owner marker: {name}')
        if not public_email not in text:
            raise VerificationError(f'Public email marker: {name}')
        if p.suffix == '.json':
            json.loads(text)
        if p.suffix == '.md':
            for link in re.findall('\\]\\(([^)]+)\\)', text):
                target = link.strip('<>').split('#')[0]
                if not target or ':' in target:
                    continue
                q = (p.parent / target).resolve()
                rel = q.relative_to(root.resolve()).as_posix()
                if not (rel in FILES or rel == MANIFEST):
                    raise VerificationError(f'Unpackaged link: {name}: {target}')
    meta = json.loads((root / RELEASE / 'release.json').read_text())
    if not (meta['release'] == 'ALPHA_007' and meta['codename_en'] == 'JULIA'):
        raise VerificationError('Validation contract failed')
    if not (meta['version'] == VERSION and meta['prerelease']['label'] == VERSION):
        raise VerificationError('Validation contract failed')
    if not (meta['prerelease']['number'] == 2 and meta['license'] == 'MIT'):
        raise VerificationError('Validation contract failed')
    if not meta['previous_release']['version'] == '007.1':
        raise VerificationError('Validation contract failed')
    if not meta['github_repository_status'] == 'NOT_PUBLISHED_BY_THIS_BUILD':
        raise VerificationError('Validation contract failed')
    if not meta['runtime_scope'] == 'INCLUDED_IN_PRIVATE_CLAUDE_EXPORT':
        raise VerificationError('Validation contract failed')
    if not meta['repository_url'] is None:
        raise VerificationError('Validation contract failed')
    master = json.loads((root / 'canon/CORE_MASTER.json').read_text(encoding='utf-8'))
    if not (master['version'] == VERSION and master['codename'] == 'JULIA'):
        raise VerificationError('Validation contract failed')
    pointer = json.loads((root / 'pointer/CURRENT_POINTER.json').read_text(encoding='utf-8'))
    if not (pointer['artifact_revision'] == 3 and pointer['build_id'] == '0.7.2-r3-architecture-foundation'):
        raise VerificationError('CLAUDE_POINTER_VERSION_DRIFT')
    if pointer['authority']['shared_protocol_source']['sha256'] != hashlib.sha256((root / 'canon/CORE_MASTER.json').read_bytes()).hexdigest():
        raise VerificationError('CLAUDE_POINTER_CORE_HASH_DRIFT')
    compact_save = json.loads((root / 'compact_state/SAVE.json').read_text(encoding='utf-8'))
    compact_hash = compact_save.pop('content_hash')
    compact_raw = (json.dumps(compact_save, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    if compact_hash != hashlib.sha256(compact_raw).hexdigest() or len(compact_save['decisions']) != 25:
        raise VerificationError('COMPACT_SAVE_INTEGRITY_OR_COUNT')
    compact_sync = json.loads((root / 'compact_state/SYNC.json').read_text(encoding='utf-8'))
    if not (compact_sync['canonical_target_build'] == pointer['build_id'] and compact_sync['counts'] == {'PENDING': 1} and compact_sync['unresolved'] == 1):
        raise VerificationError('COMPACT_SYNC_STATUS_DRIFT')
    rules = master['required_rules']
    ids = [r['id'] for r in rules]
    if not (len(ids) == len(set(ids)) and set(ids) == set(REQUIRED_RULE_IDS)):
        raise VerificationError('REQUIRED_CANON_SET_MISMATCH')
    if not all((r.get('required') is True and r.get('source') for r in rules)):
        raise VerificationError('Validation contract failed')
    if not all((isinstance(r.get(lang), str) and r[lang].strip() for r in rules for lang in LANGUAGES)):
        raise VerificationError('Validation contract failed')
    if not 'НЕ ЛЕЙ ВОДУ. НЕ ПИЗДИ. НЕ ПИЛИ.' in next((r['ru'] for r in rules if r['id'] == 'COMMUNICATION.RU.001')):
        raise VerificationError('Validation contract failed')
    if not all((x in master['preserved_core_bodies']['ru'] for x in ('Режим A', 'Режим B', 'Режим C', 'WAY_6BG_3MAIN_001'))):
        raise VerificationError('Validation contract failed')
    compile_core(root, check=True)
    validation = json.loads((root / RELEASE / 'VALIDATION.json').read_text())
    if not (validation['version'] == VERSION and validation['historical_reviews_are_current'] is False):
        raise VerificationError('Validation contract failed')
    for key in ('chatgpt_live', 'claude_live', 'full_behavioral_suite', 'independent_translation_review'):
        if not validation[key] == 'NOT_RUN_FOR_0_7_2_HASH':
            raise VerificationError(('FALSE_ACCEPTANCE', key))
    if not validation['independent_technical_review'] == 'PENDING_FOR_0_7_2_HASH':
        raise VerificationError('Validation contract failed')
    registry_result = validate_registry(root, master)
    if master.get('artifact_revision') != 3 or meta.get('artifact_revision') != 3:
        raise VerificationError('ARTIFACT_REVISION_DRIFT')
    status = json.loads((root / RELEASE / 'PRODUCT_MAP_STATUS.json').read_text())
    if status['verification_status'] != 'SOURCE_DEFINITIONS_RECOVERED':
        raise VerificationError('SOURCE_MAP_STATUS_DRIFT')
    if meta['product_map'].get('enumerated_mechanisms_verified') != 77 or meta['product_map'].get('count_is_current_release_gate') is not True:
        raise VerificationError('FALSE_OR_DISABLED_77_GATE')
    provenance = json.loads((root / RELEASE / 'SOURCE_PROVENANCE.json').read_text())
    if not (provenance['version'] == VERSION and provenance['build_source'] == 'canon/CORE_MASTER.json'):
        raise VerificationError('Validation contract failed')
    if not provenance['full_computer_merge'] == 'NOT_EXECUTED_IN_THIS_ENVIRONMENT':
        raise VerificationError('Validation contract failed')
    reconciliation = json.loads((root / 'canon/RECONCILIATION.json').read_text())
    if not reconciliation['version'] == VERSION:
        raise VerificationError('Validation contract failed')
    item_ids = [r['id'] for r in reconciliation['items']]
    if not (len(item_ids) == len(set(item_ids)) and set(REQUIRED_RULE_IDS).issubset(item_ids)):
        raise VerificationError('Validation contract failed')
    if not reconciliation['complete_private_master_merged'] is False:
        raise VerificationError('Validation contract failed')
    if not '@r00t0001' in (root / '.github/CODEOWNERS').read_text():
        raise VerificationError('Validation contract failed')
    if master['authoring_authority'] != 'canon/CORE_MASTER.json':
        raise VerificationError('SOURCE_AUTHORITY_DRIFT')
    expected_actual=set(FILES)|{MANIFEST}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()
        and not any(x in p.relative_to(root).parts for x in ('.git','dist','__pycache__'))}
    if not actual.issubset(expected_actual):
        raise VerificationError('UNEXPECTED_SOURCE_MEMBERS: '+str(actual-expected_actual))
    scenario_sets = []
    for lang in LANGUAGES:
        folder = root / RELEASE / 'locales' / lang
        if not all(((folder / f).is_file() for f in LOCALE_FILES)):
            raise VerificationError('Validation contract failed')
        core = (folder / 'CORE.txt').read_text()
        if core.count('END_P1AY_CORE_PORTABLE_ALPHA_007') != 1:
            raise VerificationError('DUPLICATE_CORE_END_MARKER')
        if not core.rstrip().endswith('END_P1AY_CORE_PORTABLE_ALPHA_007'):
            raise VerificationError('Validation contract failed')
        if not core.splitlines()[0] == 'P1▶Y · ALPHA_007 / JULIA · 0.7.2 · R3 · 2026-09-24':
            raise VerificationError('VERSION_HEADER_DRIFT')
        if not ('PRERELEASE V5' not in core and 'P1▶️Y' not in core):
            raise VerificationError('STALE_BRAND_OR_VERSION')
        for rule in rules:
            if not ('[' + rule['id'] + ']' in core and rule[lang] in core):
                raise VerificationError(('MISSING_CANON', lang, rule['id']))
        for token in ('PROGRESSION_TIER_CLASSIFIER_001', 'WAY_6BG_3MAIN_001', 'PRIVATE_PENDING_SELECTION', 'PAUSED', 'UNCLASSIFIED_REWARD_CANDIDATE', 'BUSINESS', 'ART', 'ART0', 'LEGACY', 'UNKNOWN', '0 ▶️ 1 ▶️ 2 ▶️ ∞'):
            if not token in core:
                raise VerificationError((lang, token))
        if not all((axis + ':' in core for axis in ('Scope', 'Verification', 'Durability', 'Impact'))):
            raise VerificationError(lang)
        if not 'GOVERNANCE_MODEL' not in core:
            raise VerificationError('CORE must reference packaged REFERENCE.md')
        if not all((old not in core for old in ('01▶️2', 'PRERELEASE V2', 'PRERELEASE V3', 'PRERELEASE V4'))):
            raise VerificationError('Validation contract failed')
        systems = re.findall(r'^\d+\. ', (folder / 'SYSTEMS.md').read_text(), re.M)
        if len(systems) != 77:
            raise VerificationError('MECHANISMS_77_COUNT: ' + lang)
        historical = re.findall(r'^\d+\. ', (folder / 'SYSTEMS_53_LEGACY.md').read_text(), re.M)
        if len(historical) != 53:
            raise VerificationError('HISTORICAL_53_DRIFT: ' + lang)
        if registry_view(master['mechanism_registry'],lang).rstrip() not in core:
            raise VerificationError('MECHANISMS_77_MISSING_FROM_CORE: ' + lang)
        tests = (folder / 'TESTS.txt').read_text()
        if not all((token in tests.splitlines()[0] for token in ('SHA-256', 'PASS/FAIL/BLOCKED'))):
            raise VerificationError(lang)
        ids = re.findall('^(T\\d+[ab]?) ', tests, re.M)
        if not len(ids) == len(set(ids)) == 55:
            raise VerificationError(lang)
        scenario_sets.append(set(ids))
        scenarios = {m.group(1): m.group(2) for m in re.finditer('^(T\\d+[ab]?) (.+)$', tests, re.M)}
        parity_markers = {'en': {'T18': 'English launch', 'T19': 'No connected registry', 'T20': 'explicit Yes', 'T21': 'Second explicit Yes', 'T42': 'PAUSED'}, 'ru': {'T18': 'Английский старт', 'T19': 'без подключённого реестра', 'T20': 'Первое явное', 'T21': 'Второе явное', 'T42': 'PAUSED'}}
        for scenario_id, marker in parity_markers[lang].items():
            if not marker in scenarios[scenario_id]:
                raise VerificationError((lang, scenario_id, marker))
        if lang == 'en':
            for f in LOCALE_FILES:
                if not not re.search('[А-Яа-яЁё]', (folder / f).read_text()):
                    raise VerificationError(f'Russian text in EN: {f}')
    if not scenario_sets[0] == scenario_sets[1]:
        raise VerificationError('Validation contract failed')
    state = json.loads((root / RELEASE / 'templates/STATE_SAVE.json').read_text())
    if not state['schema_version'] == 'P1AY_SAVE_04':
        raise VerificationError('Validation contract failed')
    if not state['owner'] == {'user_id': None, 'alias': None, 'confirmed': False}:
        raise VerificationError('Validation contract failed')
    if not state['safety_state'] == 'UNKNOWN':
        raise VerificationError('Validation contract failed')
    for key in ('facts', 'hypotheses', 'quests', 'sources', 'permissions', 'pending_actions'):
        if not not state[key]:
            raise VerificationError('Validation contract failed')
    if not not validate_way_direction(state):
        raise VerificationError('Validation contract failed')
    save = json.loads((root / RELEASE / 'templates/SELECTIVE_SAVE.json').read_text())
    if not save['schema_version'] == 'P1AY_SELECTIVE_SAVE_02':
        raise VerificationError('Validation contract failed')
    if not (save['owner'] is None and save['records'] == [] and (save['full_player_included'] is False)):
        raise VerificationError('Validation contract failed')
    if not save['status'] == 'PREPARED_NOT_SENT':
        raise VerificationError('Validation contract failed')
    if not (save['scope'] == [] and save['terms'] is None and (save['duration'] is None)):
        raise VerificationError('Validation contract failed')
    if not save['consent'] == {'status': 'NOT_GRANTED', 'confirmed_at': None, 'evidence': []}:
        raise VerificationError('Validation contract failed')
    if not save['owner_confirmation'] == {'status': 'NOT_CONFIRMED', 'confirmed_at': None}:
        raise VerificationError('Validation contract failed')
    if not (save['provenance'] == [] and save['transfer_evidence'] == []):
        raise VerificationError('Validation contract failed')
    if not save['revocation'] == {'status': 'NOT_REQUESTED', 'requested_at': None, 'effective_at': None}:
        raise VerificationError('Validation contract failed')
    communication = (root / RELEASE / 'templates/COMMUNICATION.txt').read_text()
    if not all((status in communication for status in ('PROPOSED', 'PREPARED_NOT_SENT'))):
        raise VerificationError('Validation contract failed')
    for lang in LANGUAGES:
        core = (root / RELEASE / 'locales' / lang / 'CORE.txt').read_text()
        if not all((value in core for value in ('UNKNOWN', 'ANALYZE', 'PAUSED', 'PREPARED_NOT_SENT'))):
            raise VerificationError('Validation contract failed')
    if not 'REFERENCE_FULL' not in (root / RELEASE / 'locales' / 'ru' / 'CORE.txt').read_text():
        raise VerificationError('Validation contract failed')
    player = (root / RELEASE / 'templates' / 'PLAYER.txt').read_text()
    if not ('art:' in player and 'level: 0' in player and ('awards: []' in player)):
        raise VerificationError('Validation contract failed')
    if not '`ЭСТЕТ1КА · AРT_7`' in (root / RELEASE / 'locales' / 'ru' / 'CORE.txt').read_text():
        raise VerificationError('Validation contract failed')
    if not '`ARTISTRY · ART_7`' in (root / RELEASE / 'locales' / 'en' / 'CORE.txt').read_text():
        raise VerificationError('Validation contract failed')
    manifest_path = root / MANIFEST
    if require_manifest:
        manifest = json.loads(manifest_path.read_text())
        if manifest.get('version') != VERSION:
            raise VerificationError('MANIFEST_VERSION_DRIFT')
        if len(manifest['files']) != len(FILES):
            raise VerificationError('MANIFEST_DUPLICATE_OR_MISSING_ENTRIES')
        if not {r['path'] for r in manifest['files']} == set(FILES):
            raise VerificationError('Validation contract failed')
        for r in manifest['files']:
            data = (root / r['path']).read_bytes()
            if not hashlib.sha256(data).hexdigest() == r['sha256']:
                raise VerificationError(r['path'])
            if not len(data) == r['bytes']:
                raise VerificationError('Validation contract failed')
        actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and (not any((x in p.relative_to(root).parts for x in ('.git', 'dist', '__pycache__'))))}
        if not actual == set(FILES) | {MANIFEST}:
            raise VerificationError(f'Unexpected/missing public members: {actual.symmetric_difference(set(FILES) | {MANIFEST})}')
    return {'status': 'PASS', 'public_files': len(FILES), 'languages': list(LANGUAGES), 'required_restored_rule_groups_per_language': len(REQUIRED_RULE_IDS), 'prior_declared_mechanisms': 77, 'named_mechanisms': registry_result['count'], 'source_definition_parity': registry_result['source_definition_parity'], 'artifact_revision': 3, 'historical_systems_per_language': 53, 'manual_scenarios_per_language': 55, 'live_model_validation': 'NOT_RUN_FOR_0_7_2_HASH'}
if __name__ == '__main__':
    import argparse, sys
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=ROOT)
    args=ap.parse_args()
    try:
        print(json.dumps(verify(args.root.resolve()),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'FAIL','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(1)
