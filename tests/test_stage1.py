from pathlib import Path
import json

import pandas as pd

from simulation.literature_wpt import condition_at_delta, distribution_moments
from stage1_model import configuration_for, load_manifest, task_distances
from run_stage1_feasibility import STRATEGIES, grid, rho_for, worker


def test_frozen_grid_and_count():
    manifest = load_manifest()
    units = list(grid(manifest))
    assert len(units) == 5400
    assert manifest["expected_execution"]["expected_replication_rows"] == 27000
    assert set(seed for *_, seed in units) == set(range(91001, 91051))


def test_literature_wpt_normalization_and_alignment_moments():
    assert condition_at_delta(0).charge_power_kw == 3.0
    assert condition_at_delta(100).charge_power_kw == 3.0 * 1.205 / 2.495
    good = distribution_moments([0.55, 0.35, 0.10, 0, 0, 0, 0, 0])
    severe = distribution_moments([0, 0.10, 0.35, 0.30, 0.25, 0, 0, 0])
    assert good["mean_charge_power_kw"] > severe["mean_charge_power_kw"]
    assert good["mean_eta"] > severe["mean_eta"]


def test_configuration_is_manifest_based_and_stage2_absent():
    cfg = configuration_for(6, 2, 90, "Moderate")
    assert cfg["n_agvs"] == 6
    assert cfg["n_pads"] == 2
    assert cfg["task_arrival_rate_per_h"] == 90
    assert cfg["deadline_model"]["urgent_slack_s"] == 240.0
    assert cfg["c4_five_feature_weights"]["next_task_energy"] == 0.7
    assert cfg["prediction_error_steps"] == [-1, 0, 1]
    assert rho_for(cfg) > 0
    assert task_distances() == {1: 30.0, 2: 40.0, 3: 50.0, 4: 60.0, 5: 70.0}


def test_disjoint_test_seed_returns_complete_policy_set():
    rows = worker((5, 1, 75, "Good", 92003))
    frame = pd.DataFrame(rows)
    assert len(frame) == 5
    assert set(frame.strategy) == set(STRATEGIES)
    assert frame.replication.nunique() == 1
    assert int(frame.replication.iloc[0]) == 92003
    assert not frame.low_soc_stops.isna().any()
