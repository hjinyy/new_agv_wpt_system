from __future__ import annotations

"""[3]-based experimental WPT charging-condition lookup for the active DES.

The table supplies relative output-power degradation and measured efficiency, not a
claim that [3]'s EV hardware is the simulated AGV hardware.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "data" / "wpt_reference" / "jeebklum_imura_sumpavakup_2026_table2_misalignment_measurements.csv"
NOMINAL_PAD_POWER_KW = 3.0


@dataclass(frozen=True, slots=True)
class WptCondition:
    delta_mm: float
    eta: float
    normalized_power: float
    charge_power_kw: float
    usable: bool


def measurement_table() -> pd.DataFrame:
    table = pd.read_csv(TABLE_PATH)
    required = {"delta_mm", "pout_mean_kw", "eta_mean_percent"}
    if not required.issubset(table.columns):
        raise ValueError(f"Reference table missing {required - set(table.columns)}")
    aligned = float(table.loc[table.delta_mm == 0, "pout_mean_kw"].iloc[0])
    table["g_power"] = table["pout_mean_kw"] / aligned
    table["eta_fraction"] = table["eta_mean_percent"] / 100.0
    table["p_charge_kw"] = NOMINAL_PAD_POWER_KW * table["g_power"]
    return table


def condition_at_index(index: int, minimum_usable_power_kw: float = 0.0) -> WptCondition:
    table = measurement_table()
    row = table.iloc[int(index)]
    power = float(row.p_charge_kw)
    eta = float(row.eta_fraction)
    return WptCondition(float(row.delta_mm), eta, float(row.g_power), power, bool(power > minimum_usable_power_kw and eta > 0.0))


def condition_at_delta(delta_mm: float, minimum_usable_power_kw: float = 0.0) -> WptCondition:
    table = measurement_table()
    matches = table.index[np.isclose(table.delta_mm.to_numpy(float), float(delta_mm))]
    if len(matches) != 1:
        raise ValueError(f"delta {delta_mm} mm is not an experimental lookup state")
    return condition_at_index(int(matches[0]), minimum_usable_power_kw)


def distribution_moments(probabilities: Iterable[float]) -> dict[str, float]:
    table = measurement_table()
    p = np.asarray(list(probabilities), dtype=float)
    if p.shape != (len(table),) or np.any(p < 0) or not np.isclose(p.sum(), 1.0):
        raise ValueError("probabilities must be nonnegative, sum to one, and match lookup states")
    return {
        "mean_delta_mm": float(np.dot(p, table.delta_mm)),
        "mean_eta": float(np.dot(p, table.eta_fraction)),
        "mean_charge_power_kw": float(np.dot(p, table.p_charge_kw)),
        "near_zero_charge_probability": float(p[table.p_charge_kw <= 0.05].sum()),
    }


def predicted_realized_index(predicted_index: int, error_steps: int, n_states: int | None = None) -> int:
    count = len(measurement_table()) if n_states is None else int(n_states)
    return int(np.clip(int(predicted_index) + int(error_steps), 0, count - 1))
