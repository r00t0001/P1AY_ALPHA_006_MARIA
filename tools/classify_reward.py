"""Pure structural classifier; it cannot verify evidence truth or grant awards."""
AXES = ('scope', 'verification', 'durability', 'impact')


def classify(event):
    if not isinstance(event, dict):
        raise ValueError('Reward event must be an object')
    candidate = {'status': 'UNCLASSIFIED_REWARD_CANDIDATE', 'tier': None, 'points': 0}
    if (event.get('status') != 'DONE' or not all(event.get(k) for k in
        ('result', 'evidence', 'verifier', 'date', 'event_id', 'dedup_group'))
            or event.get('verifier_is_sole_self_report') is not False):
        return candidate
    scores = event.get('scores', {})
    if not isinstance(scores, dict) or any(type(scores.get(k)) is not int or not 0 <= scores[k] <= 2 for k in AXES):
        raise ValueError('Each classifier axis must be an integer 0..2')
    total = sum(scores[k] for k in AXES)
    if scores['verification'] == 0 or total == 0:
        return candidate
    points = 1 if total <= 3 else 2 if total <= 5 else 3
    return {'status': 'CLASSIFIED_NOT_POSTED', 'tier': ('I', 'II', 'III')[points-1], 'points': points}
