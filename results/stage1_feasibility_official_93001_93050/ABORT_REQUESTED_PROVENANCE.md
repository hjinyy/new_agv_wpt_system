# Official Stage 1 controlled-abort request

## Status at abort request

**ABORT REQUESTED — execution remains live pending external-shell signal delivery.**

The official run showed no durable progress after the completed one-hour read-only sampler:

- valid atomic CRN part files: `0 / 5,400`
- temporary part files: `0`
- finalized raw replication rows: `0 / 27,000`
- Stage 2 execution: `false`
- OOM / cgroup memory events: none observed
- workers: four CPU-active Python spawn workers
- official parent PID at the latest snapshot: `3386150`

The official parent is a direct child of the Hermes gateway. The agent attempted a controlled `SIGTERM`, but the execution environment's gateway safety guard blocked the command because it could terminate the gateway process tree. No signal was delivered by that blocked attempt.

## Evidence hashes at latest pre-abort snapshot

- `logs/stage1_official_93001_93050.log` SHA-256: `6b992b53af4ed2c775357cdfb165452bbabc17cbe51424355cb339c9bfd3b1f8`
- `results/stage1_feasibility_official_93001_93050/RUN_MANIFEST.json` SHA-256: `1933011458ccb169fa30affcd46a2e3f30dc1d5ed17c6e06b7de77c116c97ec2`

## Provenance determination

No valid Stage 1 raw evidence was produced. Since worker-local telemetry was absent and no durable units exist, the exact subset of `93001–93050` whose randomness may have been consumed cannot be reconstructed. The entire `93001–93050` block must therefore be treated as **retired for official evidence** and must not be reused.

## Scope preservation

No physical WPT model, DES semantics, C1–C5 policy parameter, epsilon feasibility rule, rho definition, official raw file, or Stage 2 calculation was modified by this abort request.
