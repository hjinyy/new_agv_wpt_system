#!/usr/bin/env python3
"""Non-official end-to-end persistence validation for the recovered Stage 1 runner.

Uses seeds 95001–95005 only.  It never invokes --execute and never touches an
official output root.
"""
from __future__ import annotations
from concurrent.futures import as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import traceback

from run_stage1_feasibility import executor, unit_name, valid_part, worker

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "_stage1_e2e_telemetry_validation_not_evidence"


def append(path: Path, event: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), **event}, allow_nan=False) + "\n")
        handle.flush()


def run_batch(name: str, units: list[tuple[int, int, int, str, int]], workers: int) -> dict:
    root = OUT / name
    root.mkdir(parents=True)
    (root / "parts").mkdir()
    telemetry = root / "telemetry"; telemetry.mkdir()
    parent_log = telemetry / "parent.jsonl"
    for unit in units:
        append(parent_log, {"event": "parent_submit", "unit": list(unit)})
    rows = []
    with executor(workers) as pool:
        pending = {pool.submit(worker, unit, str(root), str(telemetry)): unit for unit in units}
        for future in as_completed(pending):
            unit = pending[future]
            try:
                result = future.result()
                append(parent_log, {"event": "parent_receive", "unit": list(unit), "row_count": len(result)})
                rows.extend(result)
            except Exception:
                append(parent_log, {"event": "parent_future_exception", "unit": list(unit), "traceback": traceback.format_exc()})
                raise
    paths = [root / "parts" / unit_name(unit) for unit in units]
    if not all(valid_part(path, unit) for path, unit in zip(paths, units)):
        raise RuntimeError(f"{name}: invalid or missing atomic part")
    if len(rows) != 5 * len(units):
        raise RuntimeError(f"{name}: expected {5 * len(units)} rows, got {len(rows)}")
    for unit in units:
        records = [json.loads(line) for line in (telemetry / f"{unit_name(unit)}.jsonl").read_text().splitlines()]
        events = [record["event"] for record in records]
        required = {"worker_start", "unit_start", "worker_return", "persistence_start", "persistence_success"}
        if not required.issubset(events) or events.count("c5_call_start") == 0 or events.count("c5_call_end") == 0:
            raise RuntimeError(f"{name}: incomplete telemetry for {unit}: {sorted(set(events))}")
        starts = {record.get("policy") for record in records if record["event"] == "policy_start"}
        ends = {record.get("policy") for record in records if record["event"] == "policy_end"}
        if starts != {"C1", "C2", "C3", "C4", "C5"} or ends != starts:
            raise RuntimeError(f"{name}: incomplete policy telemetry for {unit}")
    return {"name": name, "workers": workers, "units": [list(unit) for unit in units],
            "parts": len(paths), "rows": len(rows), "telemetry_dir": str(telemetry)}


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    one = [(5, 1, 75, "Good", 95001)]
    four = [(5, 1, 75, "Good", 95002), (8, 3, 105, "Severe", 95003),
            (8, 3, 105, "Severe", 95004), (8, 3, 105, "Severe", 95005)]
    result = {"status": "PASS", "official_seed_overlap": 0,
              "thread_limits": {key: __import__('os').environ.get(key) for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "HIGHS_THREADS")},
              "one_unit": run_batch("one_unit", one, 1),
              "four_concurrent_units": run_batch("four_units", four, 4)}
    (OUT / "E2E_VALIDATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
