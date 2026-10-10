#!/usr/bin/env python3
"""Stage 1 feasibility runner.

No CAPEX, OPEX, tariff, or cost-minimization logic belongs in this file.  Reserved
seeds 91001–91050 can be consumed only with --execute; smoke mode uses 92001–92002.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys

import numpy as np
import pandas as pd

from simulation.literature_wpt import distribution_moments
from stage1_model import FrozenC4Sim, configuration_for, load_manifest, task_distances
from v2_runner import generate_common, task_energy
from v3_runner import V3Sim

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "config" / "stage1_feasibility_frozen.json"
FINAL_ROOT = ROOT / "results" / "stage1_feasibility_frozen"
SMOKE_ROOT = ROOT / "results" / "_smoke_stage1_not_evidence"
STRATEGIES = ("C1", "C2", "C3", "C4", "C5")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid(manifest: dict):
    factors = manifest["primitive_grid"]
    for n_agvs in factors["n_agvs"]:
        for n_pads in factors["n_wpt_pads"]:
            for workload in factors["task_arrival_rate_per_h"]:
                for alignment in factors["alignment_condition"]:
                    for replication in range(manifest["randomness"]["stage1_seed_block"]["start"], manifest["randomness"]["stage1_seed_block"]["end"] + 1):
                        yield int(n_agvs), int(n_pads), int(workload), str(alignment), int(replication)


def rho_for(cfg: dict) -> float:
    moments = distribution_moments(cfg["alignment_probabilities"])
    mean_task_energy = float(np.mean([task_energy(cfg, d) for d in task_distances().values()]))
    demand_kw = cfg["task_arrival_rate_per_h"] * mean_task_energy
    supply_kw = cfg["n_pads"] * moments["mean_charge_power_kw"]
    return demand_kw / supply_kw


def worker(unit: tuple[int, int, int, str, int], output_dir: str | None = None) -> list[dict]:
    """One CRN work unit: one primitive tuple/seed, all five policies."""
    n_agvs, n_pads, workload, alignment, seed = unit
    cfg = configuration_for(n_agvs, n_pads, workload, alignment)
    distances = task_distances()
    tasks, initial_soc = generate_common(cfg, seed, distances=distances, urgent_ratio=0.2)
    rho = rho_for(cfg)
    rows = []
    for strategy in STRATEGIES:
        cls = FrozenC4Sim if strategy == "C4" else V3Sim
        kwargs = {"current_distances": tuple(distances.values())} if strategy == "C4" else {}
        sim = cls(cfg, strategy, seed, tasks, initial_soc, "stage1", **kwargs)
        metrics = sim.run()
        metrics.update({
            "n_agvs": n_agvs, "n_pads": n_pads, "workload_tasks_per_h": workload,
            "alignment": alignment, "rho": rho, "manifest_sha256": sha256(MANIFEST_PATH),
        })
        rows.append(metrics)
    if output_dir:
        path = Path(output_dir) / "parts" / f"a{n_agvs}_p{n_pads}_w{workload}_{alignment.lower()}_s{seed}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, allow_nan=False), encoding="utf-8")
        tmp.replace(path)
    return rows


def validate_rows(frame: pd.DataFrame, manifest: dict) -> None:
    expected = int(manifest["expected_execution"]["expected_replication_rows"])
    if len(frame) != expected:
        raise RuntimeError(f"Expected {expected} rows, found {len(frame)}")
    factors = manifest["primitive_grid"]
    required = {"C1", "C2", "C3", "C4", "C5"}
    if set(frame.strategy) != required:
        raise RuntimeError(f"Unexpected strategy set: {set(frame.strategy)}")
    counts = frame.groupby(["n_agvs", "n_pads", "workload_tasks_per_h", "alignment", "strategy"]).size()
    if not (counts == 50).all() or len(counts) != 540:
        raise RuntimeError("Each policy-specific candidate must contain exactly 50 rows")
    if frame.low_soc_stops.isna().any() or (frame.low_soc_stops < 0).any():
        raise RuntimeError("Invalid low-SOC-stop metric")
    if not set(frame.n_agvs).issubset(set(factors["n_agvs"])):
        raise RuntimeError("Unexpected AGV count")


def run_smoke(workers: int) -> Path:
    if SMOKE_ROOT.exists():
        shutil.rmtree(SMOKE_ROOT)
    SMOKE_ROOT.mkdir(parents=True)
    # deliberately disjoint from the reserved Stage 1 seed block
    units = [(5, 1, 75, "Good", 92001), (8, 3, 105, "Severe", 92002)]
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, unit) for unit in units]
        for future in as_completed(futures):
            rows.extend(future.result())
    frame = pd.DataFrame(rows)
    if len(frame) != 10 or set(frame.replication) & set(range(91001, 91051)):
        raise RuntimeError("Smoke seed/row guard failed")
    frame.to_csv(SMOKE_ROOT / "smoke_replication_metrics.csv", index=False)
    (SMOKE_ROOT / "SMOKE_OK.json").write_text(json.dumps({
        "rows": len(frame), "seeds": sorted(frame.replication.unique().tolist()),
        "reserved_seed_overlap": 0, "stage2_economic_execution": False,
    }, indent=2), encoding="utf-8")
    return SMOKE_ROOT


def execute(workers: int) -> Path:
    manifest = load_manifest()
    if manifest["stage2_gate"]["status"] != "NOT_FROZEN_NOT_AUTHORIZED":
        raise RuntimeError("Stage 2 gate unexpectedly changed")
    if FINAL_ROOT.exists():
        raise FileExistsError(f"Refusing to overwrite immutable Stage 1 root: {FINAL_ROOT}")
    units = list(grid(manifest))
    if len(units) != 5400:
        raise RuntimeError(f"Expected 5400 CRN work units, got {len(units)}")
    FINAL_ROOT.mkdir(parents=True)
    (FINAL_ROOT / "parts").mkdir()
    run_manifest = {
        "status": "RUNNING",
        "stage": "Stage 1 cost-free feasibility screening",
        "stage1_config_sha256": sha256(MANIFEST_PATH),
        "reserved_seeds": list(range(91001, 91051)),
        "expected_crn_work_units": len(units),
        "expected_replication_rows": 27000,
        "workers": workers,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "stage2_economic_execution": False,
    }
    (FINAL_ROOT / "RUN_MANIFEST.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    complete = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, unit, str(FINAL_ROOT)) for unit in units]
        for future in as_completed(futures):
            future.result()
            complete += 1
            if complete % 25 == 0 or complete == len(units):
                print(f"STAGE1_PROGRESS {complete}/{len(units)}", flush=True)
    part_paths = sorted((FINAL_ROOT / "parts").glob("*.json"))
    if len(part_paths) != len(units):
        raise RuntimeError(f"Expected {len(units)} durable CRN part files, found {len(part_paths)}")
    rows = []
    for path in part_paths:
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    frame = pd.DataFrame(rows)
    validate_rows(frame, manifest)
    raw_dir = FINAL_ROOT / "raw"
    raw_dir.mkdir()
    raw_path = raw_dir / "replication_metrics.csv"
    frame.to_csv(raw_path, index=False)
    run_manifest.update({
        "status": "COMPLETE",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "observed_part_files": len(part_paths),
        "observed_replication_rows": len(frame),
        "raw_sha256": sha256(raw_path),
    })
    (FINAL_ROOT / "RUN_MANIFEST.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    print(f"STAGE1_COMPLETE {len(frame)}", flush=True)
    return FINAL_ROOT


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.smoke == args.execute:
        parser.error("choose exactly one of --smoke or --execute")
    if args.workers < 1:
        parser.error("workers must be positive")
    print(run_smoke(args.workers) if args.smoke else execute(args.workers))
