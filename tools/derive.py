#!/usr/bin/env python3
"""derive.py -- fold this repository's git.pp records locally.

Reads every record file in a records directory (default
.gitpp/records/) and prints the fold's result -- derived state,
conflicts, orphans, derivation order -- as canonical JSON. This is
the offline reproduction of what the gitpp-action derives in CI on
every push: same records in, same state out (verified key-for-key
against the Action's reports; see the README's run table).

The fold itself is tools/fold.py, vendored byte-identical from
SuperInstance/lane-sheets (gitpp/fold.py): a labelled minimal
Python port of the derive semantics of patchwork-quilt/git.pp-ng
src/fold.ts (via gitpp-action's lib/fold.ts). It ports derive()
only -- no checkpoints, no delta, no witness freshness.

Usage: python3 tools/derive.py [records-dir]
Stdlib only. SuperInstance.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fold  # noqa: E402


def load_records(records_dir):
    records = []
    for path in sorted(Path(records_dir).glob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    records_dir = argv[0] if argv else ".gitpp/records"
    result = fold.derive(load_records(records_dir))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
