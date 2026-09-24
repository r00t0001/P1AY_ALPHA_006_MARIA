# P1AY Local Sync Runtime 0.7

A local SQLite journal for explicit SAVE synchronization. Python 3.10+; standard library only. No hosted service, implicit data upload or automatic canonical merge. Private databases, signing keys, backups and source files live outside this directory.

```sh
PYTHONPATH=. python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 -m p1ay_sync --db /private/path/state.sqlite init /private/path/identity.json
PYTHONPATH=. python3 -m p1ay_sync --db /private/path/state.sqlite status OWNER_ID
```

Run commands from this directory. `identity.json` contains an independently resolved `user_id`, `subject` and `exact_aliases`. Never derive it from an incoming filename. Existing production identity is loaded by the private registry adapter.

- [Architecture and boundaries](docs/ARCHITECTURE.md)
- [Upgrade and migration](docs/UPGRADE.md)
- [Operations, transport and restore](docs/OPERATIONS.md)
- [Privacy and release contract](docs/PRIVACY.md)

Schemas in `schemas/` are JSON Schema 2020-12 contracts for clients. Runtime validation uses explicit offline Python checks plus registered-source, identity, continuity and database checks. Schema validation alone never grants trust. Full SAVE_02/03/04 inputs that satisfy the contract can be staged; heterogeneous legacy inputs use the lossless migration envelope and require review. Selective SAVE is a distinct transport contract and cannot replace a full SAVE.

Tests exercise two synthetic peers. A real phone must be enrolled and return its own signed APPLIED receipt before the system can report peer confirmation. An unsigned Sheet row is an observation, not an authenticated state transition.
