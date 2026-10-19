# Official Stage 1 failed-execution provenance — immutable record

## Final status

**ABORTED — NO VALID STAGE 1 EVIDENCE.**

The controlled abort completed after a one-hour read-only observation found zero durable throughput. At final verification:

```text
Official runner / spawned workers: absent
Validated atomic CRN part files: 0 / 5,400
Temporary part files: 0
Final raw replication-metric rows: 0 / 27,000
Stage 2 economic execution: false
```

## Failure evidence

Workers were CPU-active in the HiGHS C5 path, and the log contained:

```text
HighsMipSolverData::transformNewIntegerFeasibleSolution tmpSolver.run();
```

No OOM, cgroup memory-limit, or durable output-write evidence was observed. Child PID replacement occurred, but the old runner did not durably record worker return, parent future receipt, unit validation, persistence success/failure, or exceptions. Therefore its exact failure path and the subset of consumed random seeds cannot be reconstructed.

## Seed disposition

`93001–93050` is **retired in full**. It must never be reused as official evidence, because one or more seeds may have been consumed without a valid durable result.

The earlier block `91001–91050` remains retired from the prior OOM-aborted attempt.

## Preserved pre-abort evidence

```text
pre-abort log SHA-256:
6b992b53af4ed2c775357cdfb165452bbabc17cbe51424355cb339c9bfd3b1f8

pre-abort RUN_MANIFEST SHA-256:
1933011458ccb169fa30affcd46a2e3f30dc1d5ed17c6e06b7de77c116c97ec2
```

## Scope preservation

No physical WPT model, DES semantic, C1–C5 policy parameter, feasibility criterion, rho definition, or Stage 2 calculation was changed during this failed execution. No valid raw simulation result exists to alter.
