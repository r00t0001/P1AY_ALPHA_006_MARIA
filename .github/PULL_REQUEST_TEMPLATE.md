## Problem

Describe the concrete problem or release requirement.

## Result

Describe the resulting behavior and affected files.

## Privacy boundary

- [ ] No real participant SAVE, profile, correspondence, credentials, private evidence or identifying screenshot is included.
- [ ] Russian and English contracts remain aligned where applicable.

## Validation

- [ ] `python3 tools/verify_release.py`
- [ ] `python3 -m unittest discover -s tools -p 'test_*.py'`
- [ ] Exact build SHA-256 recorded for any live-model result.

## Known limitations

List anything still pending, blocked or not tested.
