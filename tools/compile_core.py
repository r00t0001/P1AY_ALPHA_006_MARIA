"""Deterministic CORE and registry compiler. --check never changes files."""
import argparse
import hashlib
import json
from pathlib import Path
from mechanism_registry import registry_view, map_status
ROOT = Path(__file__).resolve().parents[1]


def outputs(root=ROOT):
    raw=(root/'canon/CORE_MASTER.json').read_bytes()
    master=json.loads(raw)
    result={}
    digest=hashlib.sha256(raw).hexdigest()
    registry=master['mechanism_registry']
    for lang in ('ru','en'):
        intro='КАНОН ОБЩЕНИЯ И ПЕРЕНОСА' if lang=='ru' else 'COMMUNICATION AND CONTINUITY CANON'
        header=f"P1▶Y · ALPHA_007 / JULIA · {master['version']} · R{master['artifact_revision']} · {master['edition_date']}"
        blocks=[header,f'SOURCE_SHA256: {digest}']
        af=master.get('architecture_foundation')
        if af:
            title=af['name_ru'] if lang=='ru' else af['name_en']
            summary=[title, 'Normative order; existing IDs remain unchanged.' if lang=='en' else 'Нормативный порядок; существующие ID не меняются.']
            for item in af['items']:
                summary.append(f"{item['order']:02d}. {item['ref']}")
            blocks.append('\n'.join(summary))
        blocks.append(intro)
        for rule in master['required_rules']:
            blocks.append(f"[{rule['id']}]\n{rule[lang]}")
        blocks.extend([registry_view(registry,lang).rstrip(),
                       master['preserved_core_bodies'][lang],
                       'END_P1AY_CORE_PORTABLE_ALPHA_007'])
        result[f'releases/alpha-007/locales/{lang}/CORE.txt']='\n\n'.join(blocks).rstrip()+'\n'
        reference=registry_view(registry,lang)
        reference+='\n'+('Генерируется из CORE_MASTER.json; не редактировать независимо.' if lang=='ru' else 'Generated from CORE_MASTER.json; do not edit independently.')+'\n'
        reference+='\n'+master['system_operational_additions'][lang].rstrip()+'\n'
        result[f'releases/alpha-007/locales/{lang}/SYSTEMS.md']=reference
    result['CORE.md']=result['releases/alpha-007/locales/ru/CORE.txt']
    result['releases/alpha-007/MECHANISMS_77.json']=json.dumps(registry,ensure_ascii=False,indent=2)+'\n'
    result['releases/alpha-007/PRODUCT_MAP_STATUS.json']=json.dumps(map_status(registry),ensure_ascii=False,indent=2)+'\n'
    return result


def compile_core(root=ROOT,check=False):
    failures=[]
    result=outputs(root)
    for name,text in result.items():
        p=root/name
        if check:
            if not p.is_file() or p.read_bytes()!=text.encode('utf-8'):
                failures.append(name)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(text,encoding='utf-8')
    if failures:
        raise ValueError('CORE_SOURCE_DRIFT: '+', '.join(failures))
    return {'status':'PASS','mode':'CHECK' if check else 'GENERATE','files':len(result)}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--root',type=Path,default=ROOT)
    args=ap.parse_args()
    print(json.dumps(compile_core(args.root,args.check)))
