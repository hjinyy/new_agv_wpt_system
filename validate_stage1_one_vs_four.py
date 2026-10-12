#!/usr/bin/env python3
"""Smoke-only deterministic equivalence and throughput test for 1 vs 4 slots."""
from __future__ import annotations

from concurrent.futures import as_completed
import hashlib
import json
from pathlib import Path
import time

import pandas as pd

from run_stage1_feasibility import executor, smoke_units, worker

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "stage1_recovery_validation"
KEYS = ["n_agvs", "n_pads", "workload_tasks_per_h", "alignment", "replication", "strategy"]
METRICS = ["requested_tasks", "completed_tasks", "completion_rate", "mean_delay", "urgent_on_time_rate", "low_soc_stops", "fleet_min_soc", "traction_energy", "aux_energy", "wpt_input_energy", "battery_delivered_energy", "wpt_loss", "mean_efficiency", "charging_wait", "rho"]


def run(workers: int, units: list[tuple[int,int,int,str,int]]) -> tuple[pd.DataFrame, float]:
    rows = []; t0 = time.perf_counter()
    with executor(workers) as pool:
        futures = [pool.submit(worker, unit) for unit in units]
        for future in as_completed(futures): rows.extend(future.result())
    frame = pd.DataFrame(rows)[KEYS + METRICS].sort_values(KEYS).reset_index(drop=True)
    return frame, time.perf_counter() - t0


def digest(frame: pd.DataFrame) -> str:
    return hashlib.sha256(frame.to_csv(index=False, float_format="%.17g").encode()).hexdigest()


def main() -> None:
    units = smoke_units()
    serial, serial_s = run(1, units)
    parallel, parallel_s = run(4, units)
    diffs = {column: float((serial[column] - parallel[column]).abs().max()) for column in METRICS}
    report = {"smoke_seeds_only": sorted({u[-1] for u in units}), "official_seed_overlap": 0, "units": [list(u) for u in units], "rows_per_run": len(serial), "one_worker_elapsed_s": serial_s, "four_worker_elapsed_s": parallel_s, "measured_speedup_1_over_4": serial_s / parallel_s, "one_worker_kpi_sha256": digest(serial), "four_worker_kpi_sha256": digest(parallel), "max_abs_differences": diffs, "tolerance_absolute": 1e-10, "pass": all(value <= 1e-10 for value in diffs.values())}
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "ONE_VS_FOUR_DETERMINISM_AND_THROUGHPUT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]: raise SystemExit(2)

if __name__ == "__main__": main()
