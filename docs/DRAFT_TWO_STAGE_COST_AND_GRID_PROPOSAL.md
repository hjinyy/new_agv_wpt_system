# Draft co-design configuration proposal — approval required

**Status:** proposal only. It must not be used to run the DES, select a design, or state a market price before explicit approval.

## A. Two-stage procedure

1. Generate the primitive grid \((N_A,N_P,\lambda,A,\pi)\).
2. Run cost-free DES feasibility screening with 50 CRN replications per candidate.
3. Remove candidates failing the predeclared service/SOC constraints.
4. Re-evaluate only the feasible raw outcomes under low/base/high annualized economic assumptions.
5. For each controlled service level, choose the feasible minimum annualized-cost design.
6. Re-evaluate selected designs over AGV/WPT relative-CAPEX sensitivity cases.
7. Use resulting \(\rho\) as explanatory diagnostic, never as an independently manipulated decision variable.

No additional DES simulation is needed in stages 4–7 unless a new primitive-factor or operational assumption is introduced.

## B. AGV CAPEX benchmark candidates

### Public source candidates

| Source | Publicly reported range | Scope / limitation |
|---|---:|---|
| [Iben Robot 2026 guide](https://en.ibenrobot.com/article/13/1316.html) | USD 15k–80k+ | Public market guide; equipment class varies. It does not establish a Korean delivered price, integration scope, battery inclusion, or maintenance contract. |
| [AGV Network cost guide](https://www.agvnetwork.com/agv-cost-estimation-how-much-does-an-automated-guided-vehicle-cost) | Cart about USD 14k; tow tractor about USD 30k; pallet jack about USD 60k; forklift about USD 80k | Public market guide; different vehicle classes cannot be averaged into a quote. |
| [Safelog cost discussion](https://www.safelog.de/en/mobile-transport-robots-costs/) | Quote/project dependent | Vendor explanation that vehicle-only price omits system-level project costs. Useful for scope caveat, not a unit price. |

### Proposed controlled vehicle-hardware sensitivity points

The points below are not Korean prices and do not average unlike vehicle types. They represent low/light-duty, base/mid-range, and high/heavier-duty public price anchors.

- Currency base: **2026 KRW**.
- Conversion convention: **1 USD = 1,343.183 KRW**, reciprocal of the XE displayed mid-market rate `1 KRW = USD 0.00074450`, retrieved 2026-09-22. It is a transparent conversion convention, not a Korean procurement quote.

| Case | USD anchor | Converted KRW per AGV | Included | Excluded |
|---|---:|---:|---|---|
| Low | 15,000 | 20,147,750 | Vehicle hardware only, at most the vendor's standard onboard equipment | Korean logistics/import, software/FMS, site integration, tax, project engineering, separately quoted battery if excluded by vendor |
| Base | 40,000 | 53,727,334 | Controlled mid-range hardware benchmark | Same exclusions; not an observed Korean transaction |
| High | 80,000 | 107,454,668 | Higher-capability hardware benchmark | Same exclusions; not an observed Korean transaction |

## C. 3-kW industrial WPT CAPEX evidence and controlled range

### Product/source candidates

| Source | What it verifies | What it does **not** verify |
|---|---|---|
| [Wiferion etaLINK 3000](https://www.wiferion.com/en/products/etalink-3000-inductive-charging-with-3-kw/) | A 3-kW AGV/AMR inductive product class exists | No public price; quote-only |
| [Onepointech LS300-A60](https://shop.onepointech.com/products/3000w-wireless-charger/) | A 3-kW AGV/AMR wireless product class and output range | The page marks price as reference only; no procurement-equivalent installed price |
| [Tongzhu 500-W marketplace listing](https://tongzhutech.en.made-in-china.com/product/MFkTzPELXcWS/China-500W-Agv-Auto-Charger-Docking-Wireless-Charging-for-Warehousing-Agv-WCM-500-36-.html) | A 500-W component listing reports USD 500–800 per set | Not 3 kW, not an installed system, not Korean pricing, and cannot be linearly scaled into an installed-pad quote |

### Proposed installed-system sensitivity points

Because no price-equivalent public 3-kW installed product quote was identified, the following are **controlled economic assumptions**, not vendor prices. They are intentionally modeled as installed WPT-system CAPEX, including one stationary transmitter/pad, compatible vehicle receiver allocation, power electronics, local protection/cabling allowance, and installation/commissioning allowance. They exclude facility-wide electrical upgrade, FMS integration, VAT/import, and building civil works.

| Case | KRW per installed 3-kW WPT system | Ratio to base AGV CAPEX | Interpretation |
|---|---:|---:|---|
| Low | 10,000,000 | 0.186 | Lower-bound installed-system sensitivity; **not** component-only price |
| Base | 25,000,000 | 0.465 | Central controlled sensitivity point; **not** a market quote |
| High | 50,000,000 | 0.931 | High installed-system/integration sensitivity; **not** a market quote |

The WPT low/base/high values must be reported as an assumption grid. They are never to be described as Korean commercial prices or as a direct extrapolation from the 500-W listing.

## D. Annualized-equivalent cost candidates

\[
C^{ann}=\operatorname{CRF}(r,L)C^{capex}+mC^{capex},
\qquad
\operatorname{CRF}(r,L)=\frac{r(1+r)^L}{(1+r)^L-1}.
\]

| Parameter | Proposed base | Sensitivity range | Status / scope |
|---|---:|---:|---|
| Discount rate \(r\) | 8% | 5%, 8%, 12% | Controlled capital-budget sensitivity. Public AGV ROI guidance commonly gives a 7–12% hurdle range, but this is not a facility WACC estimate. |
| AGV lifetime \(L_A\) | 7 years | 5, 7, 10 years | Controlled lifecycle sensitivity; not a manufacturer warranty. |
| WPT lifetime \(L_P\) | 10 years | 7, 10, 15 years | Controlled lifecycle sensitivity; not a manufacturer warranty. |
| AGV annual maintenance \(m_A\) | 4% | 2%, 4%, 6% of CAPEX/year | Controlled O&M sensitivity. |
| WPT annual maintenance \(m_P\) | 2% | 1%, 2%, 4% of CAPEX/year | Controlled O&M sensitivity. |

## E. KEPCO electricity-cost treatment

### Primary analysis

Use the incremental AGV/WPT subsystem energy cost only:

\[
C_{\rm energy}=\sum_t r_{\rm TOU}(t)E_{\rm WPT,input}(t).
\]

The rate schedule must be copied from a specified **KEPCO official** industrial tariff cell and effective date before execution. The selected cell is an analysis scenario, not a claim about the warehouse's actual tariff.

### Demand/basic charge

Exclude demand/basic charge from the primary subsystem result because actual contract power, supply voltage, contract type, and facility base-load profile are unknown. Treat it in a sensitivity/limitation analysis:

\[
\Delta C_{\rm demand}=r_{\rm demand}\max(0,P^{\rm facility+WPT}_{\rm billing}-P^{\rm facility}_{\rm billing}).
\]

### Official source candidates

- [KEPCO Korean industrial tariff table](https://cyber.kepco.co.kr/ckepco/front/jsp/CY/E/E/CYEEHP00103.jsp)
- [KEPCO English Industrial Service tariff page](https://cyber.kepco.co.kr/ckepco/front/jsp/CY/E/E/CYEEHP00203.jsp)
- [Korea Public Data Portal: KEPCO electricity rate table](https://www.data.go.kr/en/data/15090576/fileData.do)
- [IEA Korea Electricity Security Review](https://iea.blob.core.windows.net/assets/a8539b34-fb1b-42cc-ba09-e08637a59bc1/KoreaElectricitySecurityReview.pdf)

## F. Controlled service-level requirements

These are controlled study requirements, **not** empirical industry standards.

| Level | Completion \(\epsilon_c\) | Urgent on-time \(\epsilon_u\) | Mean delay \(\epsilon_D\) | SOC requirement |
|---|---:|---:|---:|---|
| Relaxed | >=95% | >=80% | <=15 min | zero low-SOC stops |
| Nominal | >=97% | >=90% | <=10 min | zero low-SOC stops |
| Strict | >=99% | >=95% | <=5 min | zero low-SOC stops |

**Candidate stochastic screening rule:** service-rate sample mean must meet its threshold, mean-delay sample mean must meet its upper bound, and every one of 50 replications must have zero low-SOC stops. A lower-confidence-bound rule is a stricter alternative and should be sensitivity-tested, not silently substituted.

## G. Primitive factor grid

| Factor | Proposed values | Levels |
|---|---|---:|
| Fleet size \(N_A\) | 5, 6, 7, 8 AGVs | 4 |
| WPT pad count \(N_P\) | 1, 2, 3 pads | 3 |
| Task arrival rate \(\lambda\) | 75, 90, 105 tasks/h (Light/Nominal/Heavy) | 3 |
| Alignment condition \(A\) | Good, Moderate, Severe | 3 |
| Charging policy \(\pi\) | C1, C2, C3, C4, C5 | 5 |

\[
4\times3\times3\times3\times5=540
\]

policy-specific primitive candidates.

With 50 CRN replications per candidate:

\[
540\times50=27{,}000
\]

DES replications in the feasibility-screening stage. Economic low/base/high application and 3×3 relative-CAPEX sensitivity reuse the same completed outcomes, so they add **zero DES replications**.

## H. Expected post-screening workflow

1. Store raw results and a completion manifest for all 27,000 screened replications.
2. For each service-level row, retain only feasible candidates.
3. Apply each coupled Low/Base/High cost case and select the annualized-cost minimum.
4. Perform a 3×3 AGV/WPT relative-CAPEX matrix on retained candidates.
5. Plot feasibility maps, cost-service frontier, selected design composition, representative SOC and WPT/fleet power flows, and rho diagnostics.
6. Reserve a new, disjoint unseen-final seed block only after all assumptions, screening rule, and selection tie-breaks are frozen.
