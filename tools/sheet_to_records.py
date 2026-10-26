# VENDORED COPY -- attribution.
#
# Vendored from SuperInstance/lane-sheets (gitpp/sheet_to_records.py,
# the lane-sheets x git.pp spike) so this repository is
# self-contained: the records under .gitpp/records/ regenerate from
# fixtures/sheet-reused.sheet.json with nothing but Python's stdlib.
#
# One adaptation from upstream: upstream imports the lane-sheets
# package (lanesheet.common) for sheet validation and all_cells().
# Here the real lanesheet.common is used when it is importable;
# otherwise small local equivalents stand in (all_cells is a flatten;
# the fallback validator checks the structural fields the converter
# reads). The conversion logic itself is unchanged, and its output
# is byte-identical to the upstream tool's. MIT -- SuperInstance.

"""sheet_to_records.py -- a lane sheet, expressed as git.pp records.

Converts one lane sheet (lane-sheets 0.1/0.2) into a directory of
git.pp-shaped records, in the layout the git.pp App and Action
consume: a records directory of `<record-id>.json` files, each one
record object {id, kind, parents, effects}.

THE MAPPING (the design content of the spike; argued in GITPP-SPIKE.md):

  * One GENESIS record per sheet, id `sheet-<sheet-id>`, kind "task",
    no parents. Its effects carry the sheet-level facts:
        sheet.id, sheet.lanesheet (format version),
        sheet.title (when present), sheet.outputs (when present),
        sheet.lanes = [{id, cells: [cell ids in order]}, ...]
    Lane structure lives HERE, as data -- lane membership and lane
    order are presentation, not derivation, so they are not ancestry.

  * One record per CELL, id `cell-<cell-id>`, kind "task" (a cell
    definition is a decision, not an observation -- it carries
    intent). Its effects carry the cell under declared keys:
        cell.<id>.kind    the cell kind (value/prompt/llm/tool/...)
        cell.<id>.def     the kind-specific payload ONLY: the cell
                          object minus id, kind, and inputs
                          (value / template / tool / equals /
                          sheet+bind+output(s))
        cell.<id>.inputs  the port map {port: source cell id}

  * PARENTS = PIPING ANCESTRY. A cell record's parents are the
    records of the cells it pipes from (its inputs' sources,
    deduplicated), or the genesis record when it pipes from nothing.
    The record DAG is therefore isomorphic to the sheet's dataflow
    DAG: the fold's dominance and tie-break machinery operates on the
    piping graph itself. The port-level truth (which port draws from
    which cell -- two ports may draw from one source) cannot live in
    parents, which are a set of ids; it lives in the
    `cell.<id>.inputs` effect. Parents say who a definition SAW;
    the inputs effect says what it PIPES.

Usage: python3 sheet_to_records.py <sheet.json> <records-dir>
Stdlib only (plus the lane-sheets package for validation).
SuperInstance.
"""

import json
import sys
from pathlib import Path

try:
    from lanesheet import common  # the real validator, when available
except ImportError:  # this repo standalone: local equivalents below
    common = None


def _all_cells(sheet):
    if common is not None:
        return common.all_cells(sheet)
    return [cell for lane in sheet["lanes"] for cell in lane["cells"]]


def _validate(sheet, sheet_path):
    if common is not None:
        common.validate_sheet(
            sheet, resolve=common.local_resolver(sheet_path.parent)
        )
        return
    # Fallback structural check: the fields convert() reads must
    # exist with the right shapes, and cell ids must be unique.
    # Full semantic validation is the lane-sheets engine's job; this
    # guards the conversion against silently producing garbage.
    if not isinstance(sheet, dict):
        raise ValueError("sheet is not a JSON object")
    for field in ("id", "lanesheet", "lanes"):
        if field not in sheet:
            raise ValueError(f"sheet is missing {field!r}")
    seen = set()
    for lane in sheet["lanes"]:
        for cell in lane["cells"]:
            if not isinstance(cell.get("id"), str) or "kind" not in cell:
                raise ValueError(f"cell lacks id/kind: {cell!r}")
            if cell["id"] in seen:
                raise ValueError(f"duplicate cell id: {cell['id']}")
            seen.add(cell["id"])

# Cell-object fields that are NOT part of the `def` payload: the id is
# the record's identity, the kind is its own declared key, and the
# inputs are the piping (record parents + the .inputs effect).
_NON_DEF_FIELDS = {"id", "kind", "inputs"}


def sheet_genesis_id(sheet):
    return f"sheet-{sheet['id']}"


def cell_record_id(cell_id):
    return f"cell-{cell_id}"


def convert(sheet):
    """A validated sheet document -> a list of git.pp records."""
    sid = sheet["id"]
    genesis = sheet_genesis_id(sheet)

    structure = [
        {"id": lane["id"], "cells": [c["id"] for c in lane["cells"]]}
        for lane in sheet["lanes"]
    ]
    g_effects = {
        "sheet.id": sid,
        "sheet.lanesheet": sheet["lanesheet"],
        "sheet.lanes": structure,
    }
    if "title" in sheet:
        g_effects["sheet.title"] = sheet["title"]
    if "outputs" in sheet:
        g_effects["sheet.outputs"] = sheet["outputs"]
    records = [
        {"id": genesis, "kind": "task", "parents": [], "effects": g_effects}
    ]

    for cell in _all_cells(sheet):
        cid = cell["id"]
        inputs = cell.get("inputs", {})
        sources = sorted({cell_record_id(src) for src in inputs.values()})
        parents = sources if sources else [genesis]
        effects = {
            f"cell.{cid}.kind": cell["kind"],
            f"cell.{cid}.def": {
                k: v for k, v in cell.items() if k not in _NON_DEF_FIELDS
            },
            f"cell.{cid}.inputs": inputs,
        }
        records.append(
            {
                "id": cell_record_id(cid),
                "kind": "task",
                "parents": parents,
                "effects": effects,
            }
        )
    return records


def write_records(records, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for rec in records:
        text = json.dumps(rec, indent=2, sort_keys=True) + "\n"
        (out / f"{rec['id']}.json").write_text(text, encoding="utf-8")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: python3 sheet_to_records.py <sheet.json> <records-dir>",
              file=sys.stderr)
        return 2
    path = Path(argv[0])
    sheet = json.loads(path.read_text(encoding="utf-8"))
    # Validate before converting: a sheet the engine would refuse is
    # refused here too, by the same names.
    _validate(sheet, path)
    records = convert(sheet)
    write_records(records, argv[1])
    print(f"{len(records)} records -> {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
