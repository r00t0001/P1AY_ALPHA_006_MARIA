# Contributing

Contributions are welcome when they preserve the public/private boundary and the evidence-gated release process.

## Before submitting

1. Do not add real participant SAVE files, profiles, correspondence, credentials, private evidence or identifying screenshots.
2. Keep Russian and English behavior aligned. Translation changes require review and must not silently change the contract.
3. Add or update a regression test for behavior or validation changes.
4. Run:

```sh
python3 tools/verify_release.py
python3 -m unittest discover -s tools -p 'test_*.py'
```

5. Describe the affected rule, evidence, expected behavior and release impact. Do not claim live-model PASS without exact prompts, responses, model/client/date and the exact archive SHA-256.

## Release artifacts

Builds use an explicit allowlist and are immutable. Never edit a built `repository` tree after its manifest and archive are generated. Make source changes first, then create a new build directory and checksum. Superseded artifacts remain clearly labeled for audit history.
