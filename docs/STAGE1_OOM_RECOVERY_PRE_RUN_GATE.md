# Stage 1 OOM-recovery pre-run gate

## Scope and semantic invariance

This recovery changes **execution infrastructure only**. It does not change the frozen physical WPT model, DES semantics, primitive grid, C1–C5 policy definitions/parameters, epsilon-feasibility filters, or rho definition.

- Frozen semantic manifest SHA-256: `01a20c820f8d85f7cac414022d9c28d4dbed448e98c210fd8bc466c43ad9f090`
- Recovery manifest SHA-256: `6e038af79f99b921b0d26ef9d4c1a57df860bcca6f75b0a2a4b654dac2ed02bf`
- Retired block: `91001–91050`; see commit `7d73d4a002932dae52a6c93eead7e4e4d572e94c`.
- New official Stage 1 seed block: `93001–93050`.

## Recovery execution implementation

- `max_tasks_per_child=1`: every primitive-condition × seed CRN unit runs in an isolated child process.
- A unit generates the common realization once and sequentially evaluates C1–C5.
- Exactly five unit rows are validated before an atomic durable JSON part-file rename.
- A resume skips only an already valid complete part; a partial/invalid part is a hard error.
- Solver records exist only within the child process and are released when it exits.
- Stage 2 economic code is absent from the runner and remains unauthorized.

## Validation pass: smoke-only seeds

The validation used only `94001–94002`; official-seed overlap was zero.

| Criterion | Observed result | Pass |
|---|---:|:---:|
| C5 1-worker full C1–C5 | 10 rows, completed twice | yes |
| 1-worker first peak cgroup | 282,996,736 bytes | yes |
| 1-worker repeat peak cgroup | 282,542,080 bytes | yes |
| Child worker release after pool close | no simulation-worker PID remained | yes |
| Memory release | 124,080,128 / 126,390,272 bytes after runs | yes |
| C5 2-worker stress peak cgroup | 399,642,624 bytes | yes |
| C5 3-worker stress peak cgroup | 549,416,960 bytes | yes |
| C5 4-worker stress peak cgroup | 701,816,832 bytes | yes |
| 4-worker post-run cgroup | 125,521,920 bytes; no live worker | yes |
| 70% cgroup threshold | 3,006,477,107 bytes of 4,294,967,296 | yes |
| 1↔2-worker KPI equivalence | max abs diff = 0 for all audited core KPIs | yes |
| 1↔4-worker KPI equivalence | identical KPI SHA-256; max abs diff = 0 | yes |

The audited 1-worker vs 2-worker and 1-worker vs 4-worker core KPIs were requested/completed tasks, completion, mean delay, urgent on-time, low-SOC stops, fleet-min SOC, traction/auxiliary/WPT energy, WPT loss/efficiency, charging wait, and rho. Tolerance was absolute `1e-10`; each observed difference was zero.

## Official execution selection

- Official workers: **4**
- C5 concurrency: **4**, admitted by full four-worker stress, child-memory release, and exact 1-versus-4-worker KPI equivalence.
- Expected work: `5,400` isolated CRN units, `27,000` replication rows.
- Throughput evidence: matching smoke units took 666.04 s on one worker and 314.01 s on four workers, a measured **2.12×** speedup. The official runtime remains scenario-dependent; the prior two-worker estimate is superseded by monitored progress once official execution begins.

This document is a pre-run gate. It is not Stage 1 evidence and contains no official simulation result.
