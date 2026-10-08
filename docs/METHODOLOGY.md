# Methodology: simulation-based epsilon-constraint co-design

## System boundary

The primary study boundary is **AGV fleet + WPT infrastructure + electricity tariff**. PV/ESS is intentionally excluded from the first co-design study and may be added only as a separately versioned extension.

## Primitive design space

\[
x=(N_A,N_P,\lambda,A,\pi)
\]

where \(N_A\) and \(N_P\) are integer infrastructure decisions, \(\lambda\) is task-arrival rate, \(A\) is the controlled WPT alignment-sensitivity condition, and \(\pi\) is the charging policy.

The DES uses the experimental WPT condition relationship

\[
\delta \rightarrow \left(P_{\rm charge}(\delta),\eta(\delta)\right).
\]

Battery-side delivered energy and WPT-side input/loss are kept distinct:

\[
E_{\rm delivered}=P_{\rm charge}\Delta t,
\quad E_{\rm input}=E_{\rm delivered}/\eta,
\quad E_{\rm loss}=E_{\rm input}-E_{\rm delivered}.
\]

## Cost objective

\[
\min_x C_{\rm total}(x)
= C_{\rm AGV}^{\rm ann}(N_A)
+ C_{\rm WPT}^{\rm ann}(N_P)
+ C_{\rm electricity}(x)
+ C_{\rm maintenance}^{\rm ann}(x).
\]

All monetary assumptions require a traceable source, currency/year, and annualization method.

## Epsilon feasibility filter

A candidate is feasible only if it satisfies all predeclared constraints:

\[
R_{\rm completion}\geq\epsilon_c,
\quad R_{\rm urgent}\geq\epsilon_u,
\quad \bar D\leq\epsilon_D,
\quad \mathrm{lowSOCStops}=0.
\]

For stochastic outputs, feasibility must specify whether it is evaluated on sample means, lower confidence bounds, or a replication-wise reliability criterion. The choice is frozen before execution.

## Selection

For each workload/alignment condition and epsilon-service level, select the feasible candidate with minimum annualized total cost. Ties are resolved by predeclared service-risk and energy criteria.

## Required figures

1. Overall co-design framework schematic.
2. AGV–WPT feasibility map.
3. Cost–service Pareto frontier.
4. Minimum-cost design composition.
5. Representative AGV SOC trajectories with 15% and 20% limits.
6. Fleet battery-side and WPT-side power flow.

No result or figure is generated until the economic model and experimental factor grid are frozen.
