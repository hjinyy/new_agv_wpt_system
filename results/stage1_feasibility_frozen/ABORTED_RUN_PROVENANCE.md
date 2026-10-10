# Stage 1 aborted-run provenance record

## Status

**ABORTED — no valid Stage 1 evidence produced.**

- Run attempted: `python3 run_stage1_feasibility.py --execute --workers 4`
- Frozen configuration SHA-256: `01a20c820f8d85f7cac414022d9c28d4dbed448e98c210fd8bc466c43ad9f090`
- Durable CRN part files: `0 / 5,400`
- Durable replication rows: `0 / 27,000`
- `raw/replication_metrics.csv`: not created
- Stage 2 economic execution: not performed.

## Failure evidence

The Linux kernel reported `memory.oom.group` for the Hermes worker cgroup with a 4 GiB memory limit. Four concurrent SciPy/HiGHS MILP workers collectively exceeded this cgroup limit and the kernel terminated the entire process group (`exit code -9`). This is a resource failure, not a model result.

## Seed provenance

The runner dispatch order begins with the four units below, one per worker:

| Unit | Primitive condition | Seed | Provenance status |
|---:|---|---:|---|
| 1 | 5 AGVs, 1 pad, 75 task/h, Good | 91001 | potentially consumed; no durable result |
| 2 | 5 AGVs, 1 pad, 75 task/h, Good | 91002 | potentially consumed; no durable result |
| 3 | 5 AGVs, 1 pad, 75 task/h, Good | 91003 | potentially consumed; no durable result |
| 4 | 5 AGVs, 1 pad, 75 task/h, Good | 91004 | potentially consumed; no durable result |

Because a seed that has driven even an in-memory simulation cannot be called pristine, **91001–91004 are retired**. The original `91001–91050` block must not be presented as a single pristine 50-replication Stage 1 block.

The remaining numbers in the block were queued but have no durable execution evidence. They are not used for restart until an explicit reseed decision.

## Required recovery decision

Do not resume automatically. A valid recovery requires a new disjoint 50-seed block and a memory-safe runner update. The proposed update uses isolated child processes (`max_tasks_per_child=1`) and at most two concurrent workers, so a HiGHS process cannot accumulate memory across multiple CRN units and the process group remains below the 4 GiB cgroup limit. This changes execution infrastructure only, not the frozen physical/DES/policy/service methodology.
