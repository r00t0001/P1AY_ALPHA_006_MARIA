"""Verify the recovered 77-item source contract, not a heading or inferred count.

This checks source definitions and generated text, not implemented services or
live AI behavior. The full private conversation is not part of this package.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

EXPECTED = {'original_source_sha256': '984efe1e5ac336492e29f67ae8130e1baccd41244fad608d89844f0ca9cf2729', 'excerpt_sha256': '6f9727358ca924fdddef254bee588677dacce9c6ae43ae1b0595c85f45f9f8ea', 'correction_sha256': '7718ddd2310947361d953485edc8e60de339cd562ad30c763dc00c6f15e614f1', 'approval_sha256': 'b7103fa338d340a3b06273aaeb42981916f4b0e7a8f9d914766b6f22c5b26272', 'semantic_payload_sha256': '24488f6a29dcbe33502cf5a91affa32ff5f9d3e3559b10c1c2e8d5d77c386524', 'group_counts': [11, 11, 14, 14, 4, 6, 12, 5], 'all_ids': ['M001', 'M002', 'M003', 'M004', 'M005', 'M006', 'M007', 'M008', 'M009', 'M010', 'M011', 'M012', 'M013', 'M014', 'M015', 'M016', 'M017', 'M018', 'M019', 'M020', 'M021', 'M022', 'M023', 'M024', 'M025', 'M026', 'M027', 'M028', 'M029', 'M030', 'M031', 'M032', 'M033', 'M034', 'M035', 'M036', 'M037', 'M038', 'M039', 'M040', 'M041', 'M042', 'M043', 'M044', 'M045', 'M046', 'M047', 'M048', 'M049', 'M050', 'M051', 'M052', 'M053', 'M054', 'M055', 'M056', 'M057', 'M058', 'M059', 'M060', 'M061', 'M062', 'M063', 'M064', 'M065', 'M066', 'M067', 'M068', 'M069', 'M070', 'M071', 'M072', 'M073', 'M074', 'M075', 'M076', 'M077']}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_original(text: str) -> list[dict]:
    records = []
    group = 0
    for line in text.splitlines():
        if line.startswith('## '):
            group += 1
        m = re.fullmatch(r'(\d+)\. \*\*(.+?)\*\* — (.+)', line.rstrip())
        if m:
            n = int(m.group(1))
            records.append({'id': f'M{n:03}', 'number': n,
                            'group_id': f'G{group:02}', 'name': m.group(2),
                            'definition_ru': m.group(3)})
    return records


def validate_registry(root: Path, master: dict) -> dict:
    def require(condition, message):
        if not condition:
            raise ValueError('MECHANISM_REGISTRY: ' + message)
    registry = master.get('mechanism_registry')
    require(isinstance(registry, dict), 'missing original named registry')
    source = registry.get('source')
    require(isinstance(source, dict), 'source provenance missing')
    require(source.get('original_file_sha256') == EXPECTED['original_source_sha256'], 'source identity drift')
    for path_key, hash_key in [('excerpt_path','excerpt_sha256'),
                               ('correction_path','correction_sha256'),
                               ('approval_path','approval_sha256')]:
        path = source.get(path_key)
        require(isinstance(path, str), 'missing source path')
        resolved = (root / path).resolve()
        require(resolved.is_relative_to(root.resolve()), 'source escapes package')
        require(sha(resolved.read_bytes()) == EXPECTED[hash_key] == source.get(hash_key), hash_key + ' mismatch')
    original = parse_original((root / source['excerpt_path']).read_text(encoding='utf-8'))
    require([x['id'] for x in original] == EXPECTED['all_ids'], 'original numbering is incomplete')
    original[17]['definition_ru'] = 'переносимое и проверяемое состояние системы.'
    correction = (root / source['correction_path']).read_text(encoding='utf-8')
    require('portable and verifiable system state.' in correction, 'last English SAVE correction missing')
    items = registry.get('mechanisms')
    require(isinstance(items,list) and len(items) == 77, 'expected 77 named records')
    require(type(registry.get('count')) is int and registry['count'] == 77, 'declared count differs')
    require(all(isinstance(x,dict) for x in items), 'non-object mechanism')
    require([x.get('id') for x in items] == EXPECTED['all_ids'], 'missing, duplicated or reordered IDs')
    require(all(type(x.get('number')) is int for x in items), 'invalid numeric ID type')
    require([x['number'] for x in items] == list(range(1,78)), 'original numbers changed')
    for x in items:
        for key in ('name','name_en','group_id','definition_ru','definition_en'):
            require(isinstance(x.get(key),str) and bool(x[key].strip()), f"{x.get('id')}: missing {key}")
        require(x.get('external_runtime_validation') == 'NOT_CLAIMED', 'unproved runtime certification')
        require(isinstance(x.get('source'),dict) and x['source'].get('original_file_sha256') == EXPECTED['original_source_sha256'], 'record source missing')
        require(type(x['source'].get('line')) is int and 432 <= x['source']['line'] <= 529, 'record source line missing')
    payload = [{k:x[k] for k in ('id','number','group_id','name','definition_ru')} for x in items]
    require(payload == original, 'source name, group or corrected definition drift')
    digest = sha(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
    require(digest == EXPECTED['semantic_payload_sha256'], 'pinned definition contract differs')
    translated = [{k:x[k] for k in ('id','name_en','definition_en')} for x in items]
    translation_digest = sha(json.dumps(translated,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'))
    require(translation_digest == 'fe82205703aabee830183009ca1f894d67cac4a1de67dc4cd6f0752bf0fc9813', 'English translation changed without contract update')
    require(items[17]['definition_en'] == 'portable and verifiable system state.', 'SAVE still describes person rather than system')
    require(items[17].get('correction',{}).get('source_line') == 560, 'SAVE correction provenance missing')
    groups = registry.get('groups')
    require(isinstance(groups,list) and len(groups) == 8, 'eight source sections required')
    group_ids = [f'G{i:02}' for i in range(1,9)]
    require([g.get('id') for g in groups] == group_ids, 'source section order drift')
    source_groups = re.findall(r'^## (.+)$', (root / source['excerpt_path']).read_text(encoding='utf-8'), re.M)
    require([g.get('ru') for g in groups] == source_groups, 'original section label changed')
    source_rows = [(428+i, line) for i,line in enumerate((root / source['excerpt_path']).read_text(encoding='utf-8').splitlines()) if re.match(r'^\d+\. \*\*',line)]
    require([x['source']['line'] for x in items] == [i for i,_ in source_rows], 'record source line drift')
    require([sum(x['group_id']==g for x in items) for g in group_ids] == EXPECTED['group_counts'], 'source section counts drift')
    lineage=Counter(x.get('lineage',{}).get('kind') for x in items)
    require(lineage == {'RETAINED_FROM_53':52,'WAY_SPLIT':6,'ADDED_MAJOR_MECHANISM':19}, '53 minus 1 plus 6 plus 19 lineage drift')
    require(registry.get('english_translation',{}).get('status') == 'TRANSLATED_FOR_THIS_RECOVERY_NOT_HISTORICAL_EN_FILE', 'translation falsely labelled original')
    return {'count':77, 'groups':8, 'numbering':'1..77',
            'source_definition_parity':'PASS', 'save_correction':'PASS',
            'semantic_payload_sha256':digest, 'external_runtime_validation':'NOT_CLAIMED'}


def registry_view(registry: dict, lang: str) -> str:
    if lang not in ('ru','en'):
        raise ValueError('Unsupported locale')
    if lang == 'ru':
        out=['# P1▶Y · 77 механик',
             'Восстановленный утверждённый продуктовый реестр. Сохранены исходные номера, разделы и названия. В №18 применено позднейшее прямое исправление: SAVE — состояние системы.',
             'Каталог определяет механики текстового протокола. Подробные действующие правила CORE уточняют их применение, ограничения и согласие; присутствие механики не доказывает реализацию внешнего сервиса. Исторические названия в каталоге не отменяют текущие правила публичной терминологии.']
    else:
        out=['# P1▶Y · 77 mechanics',
             'Recovered approved product registry. Original numbers, sections and names are retained; the Russian label in item 62 is translated. Item 18 includes the later explicit correction: SAVE is system state.',
             'These are text-protocol mechanics. Detailed current CORE rules govern operation, boundaries and consent; an entry is not proof that an external service exists. This English description is translated for this recovery, not recovered historical English bytes, except for the explicitly confirmed SAVE definition.']
    for group in registry['groups']:
        out.append('## '+group[lang])
        rows=[]
        for item in registry['mechanisms']:
            if item['group_id'] != group['id']:
                continue
            name=item['name'] if lang=='ru' else item['name_en']
            rows.append(f"{item['number']}. **{name}** — {item['definition_'+lang]}")
        out.append('\n'.join(rows))
    return '\n\n'.join(out).rstrip()+'\n'


def map_status(registry: dict) -> dict:
    return {'schema_version':'P1AY_PRODUCT_MAP_STATUS_02',
            'prior_approved_declaration':77,
            'complete_named_map':[m['id'] for m in registry['mechanisms']],
            'verification_status':'SOURCE_DEFINITIONS_RECOVERED',
            'in_package_historical_systems':53,
            'current_authority':'canon/CORE_MASTER.json#mechanism_registry',
            'current_completeness_gate':'ORIGINAL_77_IDS_NAMES_DEFINITIONS_SOURCE_HASH_AND_GENERATED_PARITY',
            'source_sha256':registry['source']['original_file_sha256'],
            'definition_payload_sha256':EXPECTED['semantic_payload_sha256'],
            'external_runtime_validation':'NOT_CLAIMED',
            'live_model_validation':'NOT_RUN_FOR_0_7_2_HASH'}
