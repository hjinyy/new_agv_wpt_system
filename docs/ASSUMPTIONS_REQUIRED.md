# Decisions required before executing the co-design study

The repository is intentionally empty and no economic assumptions are available yet. These values must be selected from a cited source or explicitly approved as controlled sensitivity assumptions.

## 1. Monetary basis

- Currency and price year (for example, KRW in 2026).
- Discount rate and service life for annualization.
- Annual operating days/hours.

## 2. Cost model

- AGV purchase cost per vehicle and annual maintenance rate.
- WPT pad purchase/installation cost per pad and annual maintenance rate.
- Electricity tariff structure: flat price, time-of-use price, and/or demand charge.
- Whether delay / urgent-service violations have a monetary penalty or are hard constraints only.

## 3. Primitive factor grid

- Fleet range \(N_A\), e.g. 5–8.
- WPT pad range \(N_P\), e.g. 1–3.
- Workload levels \(\lambda\), e.g. light / nominal / heavy.
- Alignment conditions: Good / Moderate / Severe.
- Policies to compare: C1–C5 or a defined subset.

## 4. Epsilon service levels

- Completion thresholds \(\epsilon_c\).
- Urgent on-time thresholds \(\epsilon_u\).
- Maximum mean delay \(\epsilon_D\).
- Stochastic feasibility rule: mean-only, 95% lower confidence bound, or required fraction of feasible replications.

## 5. Repetition/seed policy

- New distinct tuning/design seeds and distinct final-unseen seeds must be reserved before simulation.
- Existing final seeds `8007–8056` are prohibited.

Once these decisions are approved, they will be written into an immutable methodology freeze and the complete DES/economic experiment can be implemented and executed.
