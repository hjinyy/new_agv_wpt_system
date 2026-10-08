# AGV–WPT Cost-Reliable Co-design

This repository studies **minimum-cost feasible co-design** of AGV fleet size, WPT pad count, and charging policy under experimentally supported, misalignment-dependent WPT charging conditions.

## Research question

> Which combination of AGV fleet size \(N_A\), WPT pad count \(N_P\), and charging policy \(\pi\) minimizes annualized total cost while meeting logistics-service and battery-safety constraints?

## Frozen methodological structure

\[
(N_A,N_P,\lambda,A,\pi) \rightarrow \mathrm{DES} \rightarrow \epsilon\text{-constraint feasibility filter} \rightarrow (N_A^*,N_P^*,\pi^*)
\]

Primitive factors:

- \(N_A\): AGV fleet size
- \(N_P\): WPT pad count
- \(\lambda\): task-arrival rate
- \(A\): Good / Moderate / Severe alignment condition
- \(\pi\): charging policy

Reported outputs include annualized cost, completion, urgent on-time rate, delay, SOC safety, WPT energy/loss, and charging adequacy \(\rho\). \(\rho\) is a diagnostic operating-region indicator, not an independently optimized decision variable.

## Guardrails

- Prior final results are reference-only and are never rerun or overwritten here.
- Final unseen seeds `8007–8056` from the prior study are never used in this repository.
- Economic values must be source-backed or explicitly approved assumptions; they are not invented.
- Every executed study stores a manifest with factor grid, seeds, cost assumptions, service constraints, software SHA, and raw-result completeness.

See `docs/METHODOLOGY.md` and `docs/ASSUMPTIONS_REQUIRED.md`.
