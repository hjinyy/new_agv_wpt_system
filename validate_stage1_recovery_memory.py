#!/usr/bin/env python3
"""Strict memory/determinism validation for the Stage 1 OOM-recovery runner.

Uses only smoke seeds.  No official seed or Stage 2 calculation is touched.
"""
from __future__ import annotations

from concurrent.futures import as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
import psutil

from run_stage1_feasibility import executor, recovery_manifest, smoke_units, worker

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "stage1_recovery_validation"


def cgroup_path() -> Path:
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        hierarchy, controllers, path = line.split(":", 2)
        if hierarchy == "0" and controllers == "":
            return Path("/sys/fs/cgroup") / path.lstrip("/")
    raise RuntimeError("Unified cgroup v2 path not found")


def cgroup_value(name: str) -> int:
    return int((cgroup_path() / name).read_text().strip())


def is_resource_tracker(process: psutil.Process) -> bool:
    try:
        return "multiprocessing.resource_tracker" in " ".join(process.cmdline())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def sample_workers(parent: psutil.Process) -> tuple[int, list[int]]:
    workers = []
    for child in parent.children(recursive=True):
        try:
            if child.is_running() and not is_resource_tracker(child):
                workers.append(child)
        except psutil.NoSuchProcess:
            pass
    return sum(proc.memory_info().rss for proc in workers), [proc.pid for proc in workers]


def observe(workers: int, units: list[tuple[int, int, int, str, int]]) -> dict:
    parent = psutil.Process()
    baseline = cgroup_value("memory.current")
    limit = cgroup_value("memory.max")
    peak_child_rss = 0
    peak_cgroup = baseline
    t0 = time.perf_counter()
    rows: list[dict] = []
    with executor(workers) as pool:
        futures = [pool.submit(worker, unit) for unit in units]
        while not all(future.done() for future in futures):
            rss, _ = sample_workers(parent)
            peak_child_rss = max(peak_child_rss, rss)
            peak_cgroup = max(peak_cgroup, cgroup_value("memory.current"))
            time.sleep(0.2)
        for future in as_completed(futures):
            rows.extend(future.result())
    # Resource tracker may persist briefly; actual worker children must have exited.
    time.sleep(2.0)
    _, worker_pids_after_close = sample_workers(parent)
    after = cgroup_value("memory.current")
    return {
        "workers": workers,
        "units": [list(unit) for unit in units],
        "rows": rows,
        "row_count": len(rows),
        "elapsed_s": time.perf_counter() - t0,
        "cgroup_limit_bytes": limit,
        "cgroup_baseline_bytes": baseline,
        "peak_child_rss_bytes": peak_child_rss,
        "peak_cgroup_bytes": peak_cgroup,
        "after_cgroup_bytes": after,
        "worker_pids_alive_after_close": worker_pids_after_close,
        "all_simulation_workers_released": len(worker_pids_after_close) == 0,
        "memory_released": after <= baseline + 268_435_456,
    }


def canonical(frame_rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(frame_rows)
    keys = ["n_agvs", "n_pads", "workload_tasks_per_h", "alignment", "replication", "strategy"]
    metrics = [
        "requested_tasks", "completed_tasks", "completion_rate", "mean_delay",
        "urgent_on_time_rate", "low_soc_stops", "fleet_min_soc", "traction_energy",
        "aux_energy", "wpt_input_energy", "battery_delivered_energy", "wpt_loss",
        "mean_efficiency", "charging_wait", "rho",
    ]
    return frame[keys + metrics].sort_values(keys).reset_index(drop=True)


def equivalence(one_rows: list[dict], two_rows: list[dict]) -> dict:
    one, two = canonical(one_rows), canonical(two_rows)
    keys = ["n_agvs", "n_pads", "workload_tasks_per_h", "alignment", "replication", "strategy"]
    if not one[keys].equals(two[keys]):
        return {"pass": False, "reason": "row-key mismatch"}
    metric_columns = [column for column in one.columns if column not in keys]
    differences = {}
    for column in metric_columns:
        a, b = one[column].to_numpy(float), two[column].to_numpy(float)
        max_abs = float(np.max(np.abs(a - b)))
        differences[column] = max_abs
    passed = all(value <= 1e-10 for value in differences.values())
    return {"pass": passed, "tolerance_absolute": 1e-10, "max_abs_differences": differences}


def slim(observation: dict) -> dict:
    return {key: value for key, value in observation.items() if key != "rows"}


def main() -> None:
    recovery = recovery_manifest()
    OUT.mkdir(parents=True, exist_ok=True)
    units = smoke_units()[:2]  # same units are used in both concurrency modes
    one = observe(1, units)
    # A repeated isolated 1-worker invocation detects retained child-memory accumulation.
    one_repeat = observe(1, units)
    two = observe(2, units)
    deterministic = equivalence(one["rows"], two["rows"])
    limit = int(two["cgroup_limit_bytes"])
    threshold = int(0.70 * limit)
    c5_two_worker_pass = two["peak_cgroup_bytes"] <= threshold
    no_accumulation = one_repeat["peak_cgroup_bytes"] <= one["peak_cgroup_bytes"] + 268_435_456
    all_released = all(observation["all_simulation_workers_released"] and observation["memory_released"]
                       for observation in (one, one_repeat, two))
    passed = all_released and no_accumulation and c5_two_worker_pass and deterministic["pass"]
    report = {
        "status": "PASS" if passed else "FAIL",
        "tested_utc": datetime.now(timezone.utc).isoformat(),
        "smoke_seeds_only": sorted({unit[-1] for unit in units}),
        "official_seed_overlap": 0,
        "max_tasks_per_child": 1,
        "single_worker_full_c1_to_c5": slim(one),
        "repeated_single_worker_memory_check": slim(one_repeat),
        "two_worker_c5_stress": slim(two),
        "two_worker_70pct_threshold_bytes": threshold,
        "two_worker_c5_peak_within_70pct": c5_two_worker_pass,
        "memory_not_accumulating": no_accumulation,
        "deterministic_equivalence_1_vs_2_workers": deterministic,
        "all_workers_released_and_memory_released": all_released,
        "official_selected_workers": 2 if passed else 1,
        "stage2_economic_execution": False,
    }
    (OUT / "MEMORY_AND_DETERMINISM_VALIDATION.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
