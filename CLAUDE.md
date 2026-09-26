# P1AY · JULIA 07 · V2 · Claude entrypoint

This archive is a complete transfer package for opening the current P1AY text
protocol in Claude. Start by reading this file, then follow the order below.

## Read order

1. `pointer/CURRENT_POINTER.json` — current version, build and authority map.
2. `canon/CORE_MASTER.json` — the only editable shared protocol authority.
3. `CORE.md` — generated Russian human-readable CORE.
4. `ARCHITECTURE_FOUNDATION.md` — approved order of the 21 architecture items.
5. `releases/alpha-007/MECHANISMS_77.json` — all 77 required mechanisms.
6. `compact_state/CORE.md`, `SYNC.json` — current compact computer state and
   synchronization status. `SAVE.json` holds the owner's actual private
   decisions payload and is intentionally excluded from this package per
   `runtime/docs/PRIVACY.md`; it exists only on the owner's own machine.
7. `runtime/README.md` and `runtime/docs/` — external local runtime contract.

## Authority rules

- Build: `0.7.2-r5-level-up-system`, artifact revision `5`.
- The architecture foundation contains 21 ordered items: 19 required rules and
  2 operational additions. Existing rule IDs were not renamed.
- All 77 mechanism IDs, names and definitions are mandatory. Missing retrieval
  never reduces this requirement.
- `CORE_MASTER.json` owns the shared protocol. Generated CORE and SYSTEMS files
  are views. Compact SAVE records project decisions and does not replace PLAYER.
- Runtime, Drive transport and text protocol are separate layers. A file PASS
  does not prove phone application, recipient acknowledgement or canon merge.
- Preserve `PENDING`, `PAUSED`, permissions, conflicts, provenance and history.
  Never silently convert UNKNOWN to zero or a pending state to success.

## Claude usage

Upload the whole ZIP to one Claude Project or conversation. Ask Claude to read
`CLAUDE.md` first and to report the build ID, 21 architecture items, mechanism
count and compact sync state before doing work. If the platform cannot inspect
the ZIP directly, unpack it and upload this file together with `CORE.md`,
`canon/CORE_MASTER.json`, `releases/alpha-007/MECHANISMS_77.json`, and
`compact_state/CORE.md` + `compact_state/SYNC.json` (not `SAVE.json`, which is
private and not part of this package).

## Verification

From the unpacked package root:

```sh
python3 tools/compile_core.py --check
python3 tools/verify_release.py
python3 -O tools/verify_release.py
python3 -m unittest discover -s tools -p 'test_*.py'
python3 -m unittest discover -s runtime/tests -p 'test_*.py'
```

The compact state intentionally remains `PENDING=1`, `unresolved=1`, and
`ONLY_EXPLICIT_RECEIPTS`. No phone receipt is claimed by this export.
