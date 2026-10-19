# Root-cause addendum — failed official Stage 1 execution

This addendum supplements, without altering, the immutable failed-execution provenance committed in `94bc9f5f9c331eef2e76a9ce3c80a6d94f5228a7`.

## Definitive failure path

The preserved official stderr log proves the following sequence:

1. The worker completed the simulation work sufficiently to reach atomic part persistence.
2. `json.dumps(rows, allow_nan=False)` encountered a non-finite diagnostic field (`NaN`).
3. The worker raised `ValueError: Out of range float values are not JSON compliant`.
4. The parent received the failed future; `future.result()` re-raised that same error.
5. No atomic part was renamed into the durable `parts/` directory.

This is a persistence serialization failure, not a valid raw result and not evidence of a changed physical/DES/policy model.

## Execution-only correction

The recovery runner now canonicalizes non-finite diagnostic values to JSON `null` before strict JSON serialization. When read into the final pandas CSV, those values remain missing values. Simulation KPIs and finite solver metrics are unchanged.

It also records per-unit JSONL telemetry for:

- primitive tuple and seed;
- worker/unit/policy start and policy end;
- C5 call start/end, DES clock, solve time, solver status, and time-limit hit;
- worker return/exception;
- parent submit/receive/future exception;
- persistence start/success/failure.

## Non-official end-to-end validation

Only seeds `95001–95005` were used.

| Test | Workers | Expected | Observed | Result |
|---|---:|---:|---:|---|
| One CRN unit | 1 | 5 rows, 1 atomic part | 5 rows, 1 part | PASS |
| Four concurrent CRN units | 4 | 20 rows, 4 atomic parts | 20 rows, 4 parts | PASS |

For the one-unit test, C5 completed 542 rolling calls; telemetry confirmed a DES clock from 0 through `40,107.8635 s` at the last rolling call and policy completion at `86,400 s`. The maximum observed solve time was `0.00986577 s`, with zero time-limit hits.

Native execution limits were confirmed as `1` for `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`, and `HIGHS_THREADS`; SciPy also forwards `threads=1` to HiGHS.

No new official Stage 1 seed block has been authorized or executed.
