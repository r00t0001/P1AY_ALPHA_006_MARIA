"""Offline contracts. No network dereferencing or inference of identity."""
import hashlib
import json
import re

SCHEMAS = {'P1AY_SAVE_02', 'P1AY_SAVE_03', 'P1AY_SAVE_04'}

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    with open(path, encoding='utf-8') as f:
        return json.load(f, object_pairs_hook=pairs, parse_constant=lambda s: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def identity_errors(doc, identity, require_id=True):
    errors = []
    owner = doc.get('owner')
    if not isinstance(owner, dict):
        return ['owner must be an object']
    if require_id and owner.get('user_id') != identity['user_id']:
        errors.append('owner.user_id must equal resolved registry ID')
    allowed = {str(v).casefold() for v in [identity['user_id'], identity.get('subject', ''), *identity.get('exact_aliases', [])] if v}
    # All identity declarations must agree. Unknown aliases are held for explicit registration.
    for key in ('owner', 'identity', 'player', 'subject'):
        value = doc.get(key)
        values = [value] if isinstance(value, str) else [value[k] for k in ('user_id','subject','registry_subject','canonical_alias','alias') if k in value and value[k] is not None] if isinstance(value, dict) else []
        for token in values:
            if not isinstance(token, str) or token.casefold() not in allowed:
                errors.append('unresolved or conflicting identity: ' + key)
    if owner.get('confirmed') is not True:
        errors.append('owner confirmation required')
    return errors

def save_errors(doc):
    if not isinstance(doc, dict):
        return ['SAVE must be an object']
    errors = []
    if doc.get('schema_version') not in SCHEMAS:
        errors.append('unknown SAVE schema; preserve as untrusted input')
    for field in ('core_version', 'updated_at'):
        if not isinstance(doc.get(field), str) or not doc[field].strip():
            errors.append(field + ' must be nonempty')
    if doc.get('safety_state') not in ('UNKNOWN','ANALYZE','PAUSED'):
        errors.append('invalid or missing safety_state')
    if not isinstance(doc.get('sources'), list) or not doc['sources'] or not all(isinstance(s,str) and s.strip() for s in doc['sources']):
        errors.append('sources must contain explicit references')
    for field in ('facts','hypotheses','quests','permissions','pending_actions','conflicts','reward_events'):
        if field in doc and not isinstance(doc[field], list):
            errors.append(field + ' must be an array')
    if not isinstance(doc.get('way_direction'), dict) and not isinstance(doc.get('quests'), list):
        errors.append('missing task structure')
    way = doc.get('way_direction')
    if isinstance(way, dict):
        if way.get('phase') not in ('NOT_STARTED','OFFERED','SELECTED','ACTIVE'):
            errors.append('invalid way phase')
        for field in ('offered_directions','selected_direction_ids','background_tasks','main_task_ids'):
            if not isinstance(way.get(field), list):
                errors.append('way_direction.'+field+' must be an array')
    def walk(v, path=''):
        if isinstance(v, list):
            ids = [x.get('id',x.get('event_id')) for x in v if isinstance(x,dict) and ('id' in x or 'event_id' in x)]
            if any(not isinstance(x,str) or not x for x in ids) or len(set(str(x) for x in ids)) != len(ids):
                errors.append('invalid/duplicate IDs: '+path)
            for i,x in enumerate(v): walk(x,path+'/'+str(i))
        elif isinstance(v,dict):
            for k,x in v.items():walk(x,path+'/'+k)
    walk(doc)
    return errors

def continuity_errors(old, new, path=''):
    """Forbid silent loss; changes require a separately recorded approval in engine."""
    errors = []
    if isinstance(old, dict):
        if not isinstance(new,dict):return ['structure removed: '+path]
        for k,v in old.items():
            if k not in new:errors.append('field removed: '+path+'/'+k)
            else:errors += continuity_errors(v,new[k],path+'/'+k)
    elif isinstance(old,list):
        if not isinstance(new,list):return ['list removed: '+path]
        # ID-bearing records can change with approval, but must remain in history.
        for item in old:
            key = next((k for k in ('id','event_id') if isinstance(item,dict) and k in item),None)
            match = next((v for v in new if isinstance(v,dict) and v.get(key)==item[key]),None) if key else None
            if key and match is not None:errors += continuity_errors(item,match,path+'/'+str(item[key]))
            elif item not in new:errors.append('history/list entry removed: '+path)
    if old == 'PAUSED' and new != old:
        errors.append('PAUSED requires a separate explicit resume workflow: '+path)
    return errors

def migrate(doc, identity):
    """Lossless envelope for legacy imports; never relabels old semantics as SAVE_04."""
    if not isinstance(doc,dict) or (doc.get('schema_version') or doc.get('schema')) not in SCHEMAS:
        raise ValueError('unknown schema; quarantine without migration')
    errors = identity_errors(doc,identity)
    if errors:raise ValueError('; '.join(errors))
    return {'schema_version':'P1AY_MIGRATION_ENVELOPE_01','owner_id':identity['user_id'],
            'source_schema':doc.get('schema_version') or doc.get('schema'),
            'source_hash':sha(doc),'payload':doc,'status':'STAGED_NOT_APPLIED',
            'pause_preserved':True,'history_preserved':True}
