#!/usr/bin/env python3
"""Memory-isolated Stage 1 feasibility runner.

This module never evaluates CAPEX, OPEX, tariff, or Stage 2 selection.  It reads
frozen study semantics from ``stage1_feasibility_frozen.json`` and reads only
execution-recovery information (official seed block, worker isolation, output root)
from ``stage1_oom_recovery_93001_93050.json``.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from simulation.literature_wpt import distribution_moments
from stage1_model import FrozenC4Sim, configuration_for, load_manifest, task_distances
from v2_runner import generate_common, task_energy
from v3_runner import V3Sim

ROOT = Path(__file__).resolve().parent
SEMANTIC_MANIFEST_PATH = ROOT / "config" / "stage1_feasibility_frozen.json"
RECOVERY_MANIFEST_PATH = ROOT / "config" / "stage1_oom_recovery_93001_93050.json"
STRATEGIES = ("C1", "C2", "C3", "C4", "C5")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recovery_manifest() -> dict:
    return json.loads(RECOVERY_MANIFEST_PATH.read_text(encoding="utf-8"))


def official_root(recovery: dict | None = None) -> Path:
    recovery = recovery_manifest() if recovery is None else recovery
    return ROOT / recovery["expected_execution"]["official_output_root"]


def unit_name(unit: tuple[int, int, int, str, int]) -> str:
    n_agvs, n_pads, workload, alignment, seed = unit
    return f"a{n_agvs}_p{n_pads}_w{workload}_{alignment.lower()}_s{seed}.json"


def official_grid(semantic: dict, recovery: dict):
    factors = semantic["primitive_grid"]
    seeds = recovery["official_stage1_seed_block"]
    for n_agvs in factors["n_agvs"]:
        for n_pads in factors["n_wpt_pads"]:
            for workload in factors["task_arrival_rate_per_h"]:
                for alignment in factors["alignment_condition"]:
                    for seed in range(seeds["start"], seeds["end"] + 1):
                        yield int(n_agvs), int(n_pads), int(workload), str(alignment), int(seed)


def rho_for(cfg: dict) -> float:
    moments = distribution_moments(cfg["alignment_probabilities"])
    mean_task_energy = float(np.mean([task_energy(cfg, d) for d in task_distances().values()]))
    return cfg["task_arrival_rate_per_h"] * mean_task_energy / (cfg["n_pads"] * moments["mean_charge_power_kw"])


def validate_unit_rows(rows: list[dict], unit: tuple[int, int, int, str, int]) -> None:
    n_agvs, n_pads, workload, alignment, seed = unit
    if len(rows) != 5 or {row["strategy"] for row in rows} != set(STRATEGIES):
        raise RuntimeError(f"CRN unit {unit} does not contain exactly C1–C5")
    for row in rows:
        if (row["n_agvs"], row["n_pads"], row["workload_tasks_per_h"], row["alignment"], row["replication"]) != unit:
            raise RuntimeError(f"CRN-unit metadata mismatch for {unit}")
        if not np.isfinite(float(row["completion_rate"])) or not np.isfinite(float(row["mean_delay"])):
            raise RuntimeError(f"Non-finite KPI in {unit}")
        if float(row["low_soc_stops"]) < 0:
            raise RuntimeError(f"Negative low-SOC stop count in {unit}")


def valid_part(path: Path, unit: tuple[int, int, int, str, int]) -> bool:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        validate_unit_rows(rows, unit)
        return True
    except Exception:
        return False


def worker(unit: tuple[int, int, int, str, int], output_dir: str | None = None) -> list[dict]:
    """One isolated CRN unit: identical realization, then C1–C5 sequentially."""
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
            "alignment": alignment, "rho": rho, "semantic_manifest_sha256": sha256(SEMANTIC_MANIFEST_PATH),
        })
        rows.append(metrics)
        # Solver records remain attached only to this simulator object and disappear when this child exits.
        del sim
    validate_unit_rows(rows, unit)
    if output_dir:
        path = Path(output_dir) / "parts" / unit_name(unit)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if valid_part(path, unit):
                raise FileExistsError(f"Refusing to overwrite existing complete CRN unit: {path}")
            raise RuntimeError(f"Invalid/partial part file requires manual provenance review: {path}")
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, allow_nan=False), encoding="utf-8")
        tmp.replace(path)  # atomic rename after all five rows validate
    return rows


def executor(workers: int) -> ProcessPoolExecutor:
    # Each CRN unit exits its worker process. This prevents HiGHS/SciPy allocations
    # from accumulating over many MILP units in one process.
    return ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1)


def validate_full_rows(frame: pd.DataFrame, semantic: dict, recovery: dict) -> None:
    if len(frame) != recovery["expected_execution"]["replication_rows"]:
        raise RuntimeError(f"Expected 27000 rows, found {len(frame)}")
    counts = frame.groupby(["n_agvs", "n_pads", "workload_tasks_per_h", "alignment", "strategy"]).size()
    if len(counts) != 540 or not (counts == 50).all():
        raise RuntimeError("Every policy-specific candidate must contain exactly 50 rows")
    official = recovery["official_stage1_seed_block"]
    if set(frame.replication) != set(range(official["start"], official["end"] + 1)):
        raise RuntimeError("Official seed set mismatch")
    if set(frame.strategy) != set(STRATEGIES):
        raise RuntimeError("Policy set mismatch")
    if (frame.low_soc_stops < 0).any() or frame.low_soc_stops.isna().any():
        raise RuntimeError("Invalid safety metrics")
    if set(frame.n_agvs) != set(semantic["primitive_grid"]["n_agvs"]):
        raise RuntimeError("Grid mismatch")


def smoke_units() -> list[tuple[int, int, int, str, int]]:
    recovery = recovery_manifest()
    conditions = recovery["stress_primitive_conditions"]
    seeds = recovery["smoke_seeds"]
    return [(c["n_agvs"], c["n_pads"], c["workload"], c["alignment"], seed)
            for c, seed in zip(conditions + [conditions[-1]], seeds)]


def run_smoke(workers: int) -> Path:
    recovery = recovery_manifest()
    root = ROOT / "results" / "_smoke_stage1_recovery_not_evidence"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    units = smoke_units()
    rows: list[dict] = []
    with executor(workers) as pool:
        futures = [pool.submit(worker, unit) for unit in units]
        for future in as_completed(futures):
            rows.extend(future.result())
    frame = pd.DataFrame(rows)
    if set(frame.replication) & set(range(93001, 93051)):
        raise RuntimeError("Smoke run overlapped official seed block")
    if len(frame) != len(units) * 5:
        raise RuntimeError("Smoke row-count failure")
    frame.to_csv(root / "smoke_replication_metrics.csv", index=False)
    (root / "SMOKE_OK.json").write_text(json.dumps({
        "rows": len(frame), "seeds": sorted(frame.replication.unique().tolist()),
        "workers": workers, "max_tasks_per_child": 1,
        "official_seed_overlap": 0, "stage2_economic_execution": False,
    }, indent=2), encoding="utf-8")
    return root


def execute(workers: int) -> Path:
    semantic, recovery = load_manifest(), recovery_manifest()
    if sha256(SEMANTIC_MANIFEST_PATH) != recovery["semantic_stage1_manifest_sha256"]:
        raise RuntimeError("Semantic frozen manifest hash mismatch")
    if semantic["stage2_gate"]["status"] != "NOT_FROZEN_NOT_AUTHORIZED":
        raise RuntimeError("Stage 2 gate unexpectedly changed")
    root = official_root(recovery)
    root.mkdir(parents=True, exist_ok=True)
    parts_dir = root / "parts"
    parts_dir.mkdir(exist_ok=True)
    units = list(official_grid(semantic, recovery))
    pending = []
    for unit in units:
        part = parts_dir / unit_name(unit)
        if part.exists():
            if valid_part(part, unit):
                continue
            raise RuntimeError(f"Invalid existing part file: {part}")
        pending.append(unit)
    run_manifest = {
        "status": "RUNNING",
        "stage": "Stage 1 cost-free feasibility screening",
        "semantic_stage1_manifest_sha256": sha256(SEMANTIC_MANIFEST_PATH),
        "recovery_manifest_sha256": sha256(RECOVERY_MANIFEST_PATH),
        "official_seeds": list(range(93001, 93051)),
        "expected_crn_work_units": len(units), "pending_at_start": len(pending),
        "expected_replication_rows": 27000, "workers": workers, "max_tasks_per_child": 1,
        "started_utc": datetime.now(timezone.utc).isoformat(), "stage2_economic_execution": False,
    }
    (root / "RUN_MANIFEST.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    complete = len(units) - len(pending)
    with executor(workers) as pool:
        futures = [pool.submit(worker, unit, str(root)) for unit in pending]
        for future in as_completed(futures):
            future.result()
            complete += 1
            if complete % 10 == 0 or complete == len(units):
                print(f"STAGE1_PROGRESS {complete}/{len(units)}", flush=True)
    paths = sorted(parts_dir.glob("*.json"))
    if len(paths) != len(units):
        raise RuntimeError(f"Expected {len(units)} valid part files, found {len(paths)}")
    rows = []
    for unit in units:
        path = parts_dir / unit_name(unit)
        if not valid_part(path, unit):
            raise RuntimeError(f"Part failed post-run validation: {path}")
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    frame = pd.DataFrame(rows)
    validate_full_rows(frame, semantic, recovery)
    raw_dir = root / "raw"; raw_dir.mkdir(exist_ok=True)
    raw_path = raw_dir / "replication_metrics.csv"
    if raw_path.exists():
        raise FileExistsError("Refusing to overwrite finalized raw results")
    frame.to_csv(raw_path, index=False)
    run_manifest.update({"status": "COMPLETE", "completed_utc": datetime.now(timezone.utc).isoformat(),
                         "observed_part_files": len(paths), "observed_replication_rows": len(frame),
                         "raw_sha256": sha256(raw_path)})
    (root / "RUN_MANIFEST.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    print(f"STAGE1_COMPLETE {len(frame)}", flush=True)
    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if args.smoke == args.execute:
        parser.error("choose exactly one of --smoke or --execute")
    if args.workers < 1 or args.workers > 4:
        parser.error("workers must be between 1 and 4 under the recovery gate")
    print(run_smoke(args.workers) if args.smoke else execute(args.workers))
