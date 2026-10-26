#!/bin/sh
# check.sh -- this repository's consistency proof, runnable offline
# and in CI (.github/workflows/check.yml).
#
#   1. Regenerate the base records from the source sheet
#      (fixtures/sheet-reused.sheet.json, via the vendored
#      tools/sheet_to_records.py) and require each generated file to
#      be byte-identical to the committed record of the same name.
#      Records added by hand on top of the generated set (the
#      override-episode record) are not regenerated -- they are
#      additions to the set, and step 2 accounts for them.
#   2. Fold ALL committed records (tools/derive.py) and require the
#      result to equal tools/expected-fold.json exactly -- derived
#      state, conflicts, orphans, and derivation order.
#
# Exit 0 only if both hold. SuperInstance.
set -eu
cd "$(dirname "$0")/.."

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 tools/sheet_to_records.py fixtures/sheet-reused.sheet.json "$tmp/records" >/dev/null
for f in "$tmp"/records/*.json; do
    name=$(basename "$f")
    if ! cmp -s ".gitpp/records/$name" "$f"; then
        echo "FAIL: regenerated $name differs from the committed record" >&2
        diff -u ".gitpp/records/$name" "$f" || true
        exit 1
    fi
done
echo "records: generated set regenerates byte-identically"

python3 tools/derive.py .gitpp/records >"$tmp/fold.json"
if ! cmp -s tools/expected-fold.json "$tmp/fold.json"; then
    echo "FAIL: committed records do not fold to tools/expected-fold.json" >&2
    diff -u tools/expected-fold.json "$tmp/fold.json" || true
    exit 1
fi
echo "fold: committed records fold to the expected state"
echo "CHECK PASS"
