#!/usr/bin/env python3
"""Non-official isolated C5 slot stress; never uses official seeds."""
from __future__ import annotations

import argparse
from concurrent.futures import as_completed
import json
from pathlib import Path
import time

import psutil

from run_stage1_feasibility import executor, smoke_units, worker


def main(workers: int) -> None:
    cg_rel = next(line.split(":", 2)[2] for line in Path("/proc/self/cgroup").read_text().splitlines()
                  if line.startswith("0::"))
    cg = Path("/sys/fs/cgroup") / cg_rel.lstrip("/")
    def mem() -> int: return int((cg / "memory.current").read_text())
    units = smoke_units()
    while len(units) < workers:
        n, p, w, a, _ = units[-1]
        units.append((n, p, w, a, 94001 + len(units)))
    units = units[:workers]
    parent = psutil.Process(); baseline = mem(); peak_cg = baseline; peak_rss = 0; rows = []; t0 = time.perf_counter()
    with executor(workers) as pool:
        futures = [pool.submit(worker, unit) for unit in units]
        while not all(future.done() for future in futures):
            children = []
            for proc in parent.children(recursive=True):
                try:
                    if proc.is_running() and "resource_tracker" not in " ".join(proc.cmdline()): children.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied): pass
            peak_rss = max(peak_rss, sum(proc.memory_info().rss for proc in children)); peak_cg = max(peak_cg, mem()); time.sleep(.2)
        for future in as_completed(futures): rows.extend(future.result())
    time.sleep(2)
    live = []
    for proc in parent.children(recursive=True):
        try:
            if proc.is_running() and "resource_tracker" not in " ".join(proc.cmdline()): live.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
    report = {"workers":workers,"official_seed_overlap":0,"seeds":sorted({unit[-1] for unit in units}),"rows":len(rows),"elapsed_s":time.perf_counter()-t0,"cgroup_path":str(cg),"baseline_cgroup_bytes":baseline,"peak_cgroup_bytes":peak_cg,"peak_child_rss_bytes":peak_rss,"after_cgroup_bytes":mem(),"live_worker_pids_after_close":live}
    out = Path(f"results/stage1_recovery_validation/{workers}_WORKER_SLOT_STRESS.json"); out.write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
    if len(rows) != 5 * workers or live: raise SystemExit(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--workers",type=int,required=True); args = parser.parse_args()
    if args.workers < 1 or args.workers > 4: parser.error("workers must be in [1,4]")
    main(args.workers)
