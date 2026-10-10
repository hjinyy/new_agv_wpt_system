"""Frozen Stage 1 DES model construction; intentionally contains no economic model."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import time

import numpy as np

from v2_runner import load_cfg, task_energy, task_time
from v3_runner import V3Sim

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "config" / "stage1_feasibility_frozen.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def configuration_for(n_agvs: int, n_pads: int, workload: int, alignment: str) -> dict:
    """Build an executable configuration strictly from the frozen Stage 1 manifest."""
    frozen = load_manifest()
    cfg = load_cfg()
    condition = frozen["alignment_conditions"][alignment]
    error = condition["prediction_error"]
    cfg.update({
        "n_agvs": int(n_agvs),
        "n_pads": int(n_pads),
        "task_arrival_rate_per_h": float(workload),
        "wpt_condition_source": "literature_reference",
        "alignment_condition": alignment,
        "alignment_probabilities": list(condition["probabilities"]),
        "prediction_error_steps": [int(value / 50) for value in error["delta_steps_mm"]],
        "prediction_error_probabilities": list(error["probabilities"]),
        "deadline_model": deepcopy(frozen["operational_model"]["deadline"]),
        "c4_five_feature_weights": deepcopy(frozen["policies"]["C4"]["weights"]),
        "c5_horizon_s": float(frozen["policies"]["C5"]["horizon_s"]),
        "c5_slot_s": float(frozen["policies"]["C5"]["slot_s"]),
        "c5_time_limit_s": float(frozen["policies"]["C5"]["time_limit_s"]),
        "c5_mip_rel_gap": float(frozen["policies"]["C5"]["mip_relative_gap"]),
        "efficiency_states": {"labels": [str(value) for value in condition["delta_mm"]], "probabilities": list(condition["probabilities"])},
    })
    return cfg


def task_distances() -> dict[int, float]:
    frozen = load_manifest()
    return {index + 1: float(value) for index, value in enumerate(frozen["operational_model"]["task_distance_m_by_picking_point"])}


class FrozenC4Sim(V3Sim):
    """The frozen C4 policy: predicted WPT condition ranks charging only."""

    def __init__(self, *args, current_distances: tuple[float, ...], **kwargs):
        super().__init__(*args, **kwargs)
        self.current_distances = current_distances
        self._priority_latencies_s: list[float] = []

    def four_features(self, agv, t: float, next_task) -> dict[str, float]:
        energy = task_energy(self.cfg, next_task.distance_m)
        duration = task_time(self.cfg, next_task.distance_m)
        quantum = self.cfg["opportunity_quantum_s"]
        detour = 2 * self.cfg["zone_pad_distance_m"] / self.cfg["agv_speed_mps"]
        expected_wait = self.cfg.get("_expected_contention_wait_s", 0.0)
        projected = max(t + detour + quantum + expected_wait, next_task.arrival) + duration
        delay = max(0.0, projected - next_task.deadline)
        idle = max(0.0, t - agv.last_job_end)
        f_soc = float(np.clip((self.cfg["max_soc"] - agv.soc) / (self.cfg["max_soc"] - self.cfg["min_soc"]), 0, 1))
        emin = task_energy(self.cfg, min(self.current_distances))
        emax = task_energy(self.cfg, max(self.current_distances))
        f_energy = 0.0 if emax <= emin else float(np.clip((energy - emin) / (emax - emin), 0, 1))
        f_idle = float(np.clip(idle / 1800.0, 0, 1))
        f_deadline = float(np.clip(delay / 600.0, 0, 1))
        condition = self.wpt_condition(next_task, agv, mode="predicted")
        f_power = float(np.clip(condition.charge_power_kw / self.cfg["wpt_power_kw"], 0, 1))
        weights = self.cfg["c4_five_feature_weights"]
        score = (weights["soc"] * f_soc + weights["next_task_energy"] * f_energy +
                 weights["idle"] * f_idle + weights["charging_power_quality"] * f_power -
                 weights["deadline"] * f_deadline)
        return {"score": score, "f_SOC": f_soc, "f_E": f_energy, "f_idle": f_idle,
                "f_P": f_power, "f_D": f_deadline}

    def choose(self, cands, t, next_task, avail_pads):
        tic = time.perf_counter()
        try:
            if self.strategy != "C4":
                return super().choose(cands, t, next_task, avail_pads)
            preview = self.preview_task_map(cands, t, next_task)
            def agv_task(agv):
                return preview.get(agv.agv_id, next_task)
            def slack(agv):
                task = agv_task(agv)
                return task.deadline - (t + task_time(self.cfg, task.distance_m))
            critical = [agv for agv in cands if agv.soc <= self.cfg["critical_soc"]]
            if critical:
                return sorted(critical, key=lambda agv: (agv.soc, slack(agv), agv.agv_id))[:avail_pads], "critical"
            scored = [(self.four_features(agv, t, agv_task(agv))["score"], agv) for agv in cands]
            return [item[1] for item in sorted(scored, key=lambda item: (-item[0], item[1].agv_id))[:avail_pads]], "C4"
        finally:
            self._priority_latencies_s.append(time.perf_counter() - tic)

    def metrics(self):
        output = super().metrics()
        latencies = np.asarray(self._priority_latencies_s, dtype=float)
        output.update({
            "priority_decisions": int(len(latencies)),
            "total_priority_computation_time_s": float(latencies.sum()),
            "mean_decision_latency_ms": float(latencies.mean() * 1000) if len(latencies) else 0.0,
        })
        return output
