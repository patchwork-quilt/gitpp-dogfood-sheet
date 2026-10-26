# Changelog

## 2026-10-26 — a complete project

The repo grows from a records stub into the project those records
encode. The six records and the verification of run 40361763003 are
untouched.

- `fixtures/` — the source sheets: `sheet-reused.sheet.json` (the
  project) and `word-frame.sheet.json` (the reusable inner sheet it
  applies twice), copied from SuperInstance/lane-sheets.
- `tools/` — the vendored compiler (`sheet_to_records.py`, with
  attribution), the offline fold (`derive.py` + `fold.py`), the
  expected fold result (`expected-fold.json`), and `check.sh`:
  regeneration must be byte-identical, the fold must match the
  expectation. Wired into CI as `.github/workflows/check.yml`.
- `docs/anatomy.svg` — the lane-sheet anatomy diagram.
- README rebuilt: runnable example first, then the model, then the
  run table and the honest limits.
- MIT LICENSE added.

## 2026-10-26 — initial dogfood

- Six git.pp records under `.gitpp/records/` generated from the
  `sheet-reused` fixture; `.github/workflows/gitpp.yml` running the
  public gitpp-action v0.3.1 on push; a README written as a
  prediction before the first run.
- Run
  [40361763003](https://github.com/patchwork-quilt/gitpp-dogfood-sheet/actions/runs/40361763003):
  success — 6 records · 20 keys · 0 conflicts · 0 orphans, agreeing
  with an independent local fold on 20/20 keys.
