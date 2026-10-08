# Economic-model evidence register and approval gate

**Status:** draft; do not use for simulation until the approval table is completed.

## What is supported by public sources

### Electricity tariff structure

For Korea industrial/commercial consumers, the electricity bill should not be represented by a single universal KRW/kWh value. The public evidence supports a two-part structure:

\[
C_{\rm elec}=C_{\rm demand}(P_{\rm billing})+\sum_t r_{\rm TOU}(t)E_{\rm grid}(t).
\]

- **KEPCO official tariff page:** [Korean industrial tariff table](https://cyber.kepco.co.kr/ckepco/front/jsp/CY/E/E/CYEEHP00103.jsp). It identifies off-peak / mid-peak / peak treatment and explains that the billing demand for relevant industrial customers is tied to the larger measured demand in the specified periods.
- **IEA, Korea Electricity Security Review:** [PDF](https://iea.blob.core.windows.net/assets/a8539b34-fb1b-42cc-ba09-e08637a59bc1/KoreaElectricitySecurityReview.pdf). It states that Korean industrial and commercial tariffs consist of a demand charge in KRW/kW-month and time-differentiated energy charges in KRW/kWh.
- **KEPCO 2024-10 revision context:** public reporting states that industrial energy charges increased by 16.1 KRW/kWh on average from 24 October 2024. This is context only, not a substitute for selecting the applicable KEPCO tariff cell.

**Required choice:** facility supply voltage, contractual industrial tariff category, tariff effective date, and whether facility base load/demand charge is inside the study boundary.

### AGV CAPEX

No reliable Korean public list price for a warehouse AGV configuration matching this DES was found. Public vendor guides demonstrate that purchase cost is highly payload/navigation/integration dependent; those guides are not a defensible facility-specific Korean quote.

**Required choice:** either (a) a vendor quotation, (b) an explicitly labelled controlled CAPEX range with low/base/high sensitivity, or (c) a source selected by the author after manual review.

### Industrial WPT pad CAPEX

No credible public Korean price for an installed 3-kW AGV WPT pad/receiver/converter package was found. Consumer wireless-charger prices and passenger-EV charger prices are not transferable.

**Required choice:** vendor quotation or an explicit controlled sensitivity range. The study must label it as a cost-model assumption rather than measured market price.

## Proposed transparency-preserving cost model

\[
C_{\rm total}^{ann}=\mathrm{CRF}(r,L_A)N_A C_A + \mathrm{CRF}(r,L_P)N_P C_P + m_A N_A C_A + m_P N_P C_P + C_{\rm elec}^{ann}
\]

where \(C_A\) and \(C_P\) are approved AGV and installed-WPT-pad CAPEX values; \(m_A,m_P\) are annual maintenance fractions; and \(\mathrm{CRF}\) is the capital-recovery factor.

## Approval table

| Item | Required final value/source | Current status |
|---|---|---|
| Currency and base year | KRW, year | Pending |
| Discount rate | annual percentage | Pending |
| AGV service life / CAPEX / maintenance | years, KRW/unit, %/year | Pending |
| WPT service life / installed CAPEX / maintenance | years, KRW/pad, %/year | Pending |
| KEPCO tariff cell | category, voltage, effective date | Pending |
| Demand charge inside boundary | yes/no | Pending |
| Base facility load | profile or excluded | Pending |
| Completion epsilon levels | percent | Pending |
| Urgent on-time epsilon levels | percent | Pending |
| Mean-delay epsilon levels | time | Pending |
| Stochastic feasibility rule | mean / lower CI / reliability fraction | Pending |
| Primitive ranges | \(N_A,N_P,\lambda,A,\pi\) | Pending |

No simulation is authorized by this document.
