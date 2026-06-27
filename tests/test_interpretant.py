"""Step-6 measure tests (pre-reg 9.5 component checks): the surplus positive control
reads > 0; an inert (gamma=0) pure-mechanism read-out reads surplus ~ 0 under both
standards; family maintenance rises with gamma; determinism under fixed seeds.

ASCII only. These test the APPARATUS, not the headline verdict (the empty-or-occupied
solution set is computed in the result/adjudication, not asserted here).
"""

import numpy as np
import pytest

from steerpush.config import CFG
from steerpush.interpretant import (
    measure_surplus,
    measure_family_maintenance,
    measure_positive_control,
    measure_error_store,
    surplus_stat,
)


# --- positive control: the measure must read surplus > 0 on a known error-corrector --
def test_positive_control_reads_surplus_positive():
    r = measure_positive_control(CFG)
    assert r["surplus"] > CFG.surplus_thresh
    assert r["surplus_positive"] is True


# --- inert (gamma=0) pure mechanism: no system-internal error under either standard ---
def test_inert_readout_surplus_zero_S1():
    r = measure_surplus(0.0, "S1", CFG)
    assert r["surplus"] < CFG.surplus_thresh
    assert r["surplus_positive"] is False


def test_inert_readout_surplus_zero_S2():
    r = measure_surplus(0.0, "S2", CFG)
    assert r["surplus"] < CFG.surplus_thresh
    assert r["surplus_positive"] is False


# --- S2 (fixed external template) grounds no system-internal error at ANY gamma -------
def test_S2_template_surplus_zero_all_gamma():
    for gamma in CFG.gamma_sweep:
        r = measure_surplus(gamma, "S2", CFG)
        assert r["surplus"] < CFG.surplus_thresh, f"S2 gamma={gamma} surplus={r['surplus']}"


# --- S1 (persistence) DOES register error once the read-out feeds back (gamma > 0) ----
def test_S1_persistence_surplus_positive_when_gamma_positive():
    r = measure_surplus(1.0, "S1", CFG)
    assert r["surplus"] > CFG.surplus_thresh
    assert r["surplus_positive"] is True


# --- maintenance rises with gamma; Deacon-PUSH only at gamma = 0 ----------------------
def test_maintenance_rises_with_gamma():
    eps = [measure_family_maintenance(g, CFG)["entropy_production"] for g in CFG.gamma_sweep]
    assert eps[0] == pytest.approx(0.0, abs=1e-9)          # gamma=0 -> drive 0 -> exactly 0
    assert all(b >= a - 1e-6 for a, b in zip(eps, eps[1:]))  # non-decreasing
    assert eps[-1] > eps[1]                                  # strictly rises across the sweep


def test_deacon_push_only_at_gamma_zero():
    assert measure_family_maintenance(0.0, CFG)["deacon_push"] is True
    for gamma in CFG.gamma_sweep[1:]:
        assert measure_family_maintenance(gamma, CFG)["deacon_push"] is False


# --- determinism ----------------------------------------------------------------------
def test_determinism_under_fixed_seed():
    a = measure_surplus(1.0, "S1", CFG)["surplus"]
    b = measure_surplus(1.0, "S1", CFG)["surplus"]
    assert a == b
    c = measure_positive_control(CFG)["surplus"]
    d = measure_positive_control(CFG)["surplus"]
    assert c == d


# --- multistable equilibrium error-store: RECORDING is not TREATING-AS-ERROR ----------
def test_error_store_records_but_does_not_treat_as_error():
    """The panel's live OCCUPY route. The store RECORDS correctness (raw surplus large)
    at zero throughput (Deacon-PUSH), but it does NOT treat false tokens AS ERROR
    (functional/persistence surplus ~ 0): an equilibrium bistable well holds either bit
    equally. So under the naive RAW correlate it would falsely occupy, but under the
    faithful 9.2 (treats-as-error) reading it does NOT occupy -> the close survives."""
    r = measure_error_store(CFG)
    assert r["raw_surplus_records_correctness"] > 1.5          # it RECORDS correctness
    assert r["functional_surplus_treats_as_error"] < CFG.surplus_thresh  # but does not act on it
    assert r["deacon_push"] is True                            # equilibrium store, zero throughput
    assert r["would_occupy_under_RAW_correlate"] is True       # the naive estimator's false positive
    assert r["occupies_under_FUNCTIONAL"] is False             # the faithful estimator closes it


# --- estimator sanity -----------------------------------------------------------------
def test_surplus_stat_zero_when_no_differential():
    rng = np.random.default_rng(0)
    cost = rng.standard_normal(1000)
    correct = rng.integers(0, 2, 1000).astype(bool)   # cost independent of correctness
    assert surplus_stat(correct, cost) < 0.2          # ~ 0 (no systematic differential)
    # a real differential is detected
    cost2 = cost + correct * 1.0
    assert surplus_stat(correct, cost2) > 0.8
