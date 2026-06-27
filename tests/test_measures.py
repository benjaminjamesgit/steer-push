"""Step-5 measure tests: the matched pair must return the predicted steer/push
signature per measure, deterministically under fixed seeds, with a zero-D /
symmetric sanity check.

ASCII only.
"""

import numpy as np
import pytest

from steerpush.config import CFG
from steerpush.dynamics import (
    make_bistable, make_monostable, make_featureless, make_driven_ring, settle,
)
from steerpush.measures import (
    measure_C1_multistability,
    measure_C2_gain,
    measure_C3_local_info,
    measure_C4_persistence,
    measure_fep_flatness,
    measure_maintenance_work,
    mutual_info_bits,
)


@pytest.fixture(scope="module")
def systems():
    latch = make_bistable(CFG.well_sep, CFG.barrier)
    mono = make_monostable(CFG.mono_stiffness)
    featureless = make_featureless(CFG.mono_stiffness)
    return latch, mono, featureless


# --- C1: multistability ---------------------------------------------------- #
def test_C1_latch_two_basins(systems):
    latch, _, _ = systems
    r = measure_C1_multistability(latch, CFG)
    assert r["n_basins"] == 2
    centers = sorted(r["basin_centers"])
    assert centers[0] == pytest.approx(-CFG.well_sep, abs=0.05)
    assert centers[1] == pytest.approx(+CFG.well_sep, abs=0.05)


def test_C1_mono_one_basin(systems):
    _, mono, _ = systems
    r = measure_C1_multistability(mono, CFG)
    assert r["n_basins"] == 1
    assert r["basin_centers"][0] == pytest.approx(0.0, abs=0.05)


# --- C2: trigger-not-drive ------------------------------------------------- #
def test_C2_latch_diverges(systems):
    latch, _, _ = systems
    r = measure_C2_gain(latch, CFG)
    assert r["diverges"] is True
    # a vanishing trigger still yields a full-size (well-scale) outcome
    assert abs(r["R_at_smallest_D"]) > 0.5 * CFG.well_sep
    assert r["outcome_well_scale"] is True
    assert r["trigger_not_drive"] is True


def test_C2_mono_finite_and_vanishes(systems):
    _, mono, _ = systems
    r = measure_C2_gain(mono, CFG)
    assert r["diverges"] is False
    assert r["trigger_not_drive"] is False
    # gain is the constant 1/kappa across the sweep
    gains = [row["gain"] for row in r["rows"]]
    assert np.allclose(gains, 1.0 / CFG.mono_stiffness, rtol=1e-3)
    # response -> baseline as D -> 0
    assert abs(r["R_at_smallest_D"]) < 1e-3


def test_C2_trigger_not_drive_rejects_sublinear_single_well():
    """A sub-harmonic single well (V = x^4) has DIVERGING gain (|R|/|D| grows) yet is a
    PUSH: the outcome vanishes with D. trigger_not_drive must reject it -- divergence
    alone is non-specific; the full-size D-independent outcome is the real signature."""
    from steerpush.dynamics import System

    def V(x):
        x = np.asarray(x, dtype=float)
        return x ** 4
    def dV(x):
        x = np.asarray(x, dtype=float)
        return 4.0 * x ** 3
    quartic = System("quartic_push", V, dV, (0.0,))
    r = measure_C2_gain(quartic, CFG)
    assert r["diverges"] is True              # |R|/|D| grows (R sublinear in D)
    assert r["outcome_well_scale"] is False   # but R -> 0 as D -> 0
    assert r["trigger_not_drive"] is False    # so NOT a steer


# --- C3: local information creation ---------------------------------------- #
def test_C3_latch_creates_bit(systems):
    latch, _, _ = systems
    r = measure_C3_local_info(latch, CFG)
    assert r["info_bits"] > 0.8          # R retains the prior internal bit


def test_C3_mono_no_bit(systems):
    _, mono, _ = systems
    r = measure_C3_local_info(mono, CFG)
    assert r["info_bits"] < 0.1          # prior washes out; R = f(D)


# --- C4: selector-persistence ---------------------------------------------- #
def test_C4_latch_remembers(systems):
    latch, _, _ = systems
    r = measure_C4_persistence(latch, CFG)
    assert r["memory_bits"] > 0.8        # set bit survives the D=0 hold
    assert r["held_fraction"] > 0.95
    assert r["bias_pulse2_bits"] > 0.8   # pulse 1 conditions pulse 2


def test_C4_mono_forgets(systems):
    _, mono, _ = systems
    r = measure_C4_persistence(mono, CFG)
    assert r["memory_bits"] < 0.1
    assert r["bias_pulse2_bits"] < 0.1


# --- FEP-flatness ---------------------------------------------------------- #
def test_fep_verdict_constant(systems):
    latch, mono, featureless = systems
    r = measure_fep_flatness((latch, mono, featureless), CFG)
    assert r["verdict_constant"] is True          # self-evidencing for all three
    assert r["n_modes_by_system"] == [2, 1, 1]    # n_modes = C1 multistability
    # self-evidencing is COMPUTED (mass near modes), not hardcoded
    assert all(rec["self_evidencing"] is True for rec in r["records"])
    assert all(rec["mode_mass"] > 0.5 for rec in r["records"])


def test_fep_escape_hatch_cannot_track_split(systems):
    """The pre-registered escape hatch is LIVE: the one native FEP scalar that is not a
    restatement of multimodality (mean surprisal) does NOT robustly separate steer/push
    -- a wide PUSH well reads HIGHER surprisal than the STEER latch. So FEP is flat."""
    latch, mono, featureless = systems
    r = measure_fep_flatness((latch, mono, featureless), CFG)
    assert r["mean_surprisal_varies"] is True                 # surprisal DOES vary...
    assert r["probe_kappa1_push_surprisal"] > r["latch_surprisal"]   # ...a PUSH exceeds the latch
    assert r["fep_can_track_split"] is False                  # so it is not a robust separator


# --- Deacon / maintenance work --------------------------------------------- #
def test_maintenance_latch_zero(systems):
    latch, _, _ = systems
    r = measure_maintenance_work(latch, CFG)
    assert r["persists_with_no_input"] is True
    assert r["drift_at_rest"] < CFG.rest_drift_tol
    assert abs(r["net_current"]) < 1.0            # ~0 net current (equilibrium)


def test_maintenance_mono_zero(systems):
    _, mono, _ = systems
    r = measure_maintenance_work(mono, CFG)
    assert r["persists_with_no_input"] is True
    assert abs(r["net_current"]) < 1.0
    assert r["entropy_production"] == pytest.approx(0.0, abs=1e-9)


def test_maintenance_driven_decoy_is_positive():
    """Positive control: the (A)/(B) guard must be able to read NONZERO. A driven
    nonequilibrium ring (f > 1) dissipates a positive housekeeping heat and does NOT
    persist without input -- so 'maintenance ~ 0' for the latch is a real measurement,
    not zero-by-construction for everything."""
    decoy = make_driven_ring()
    r = measure_maintenance_work(decoy, CFG, drive=CFG.drive_force)
    assert r["entropy_production"] > 1.0          # positive housekeeping heat
    assert abs(r["net_current"]) > 0.5            # a net steady-state current
    assert r["persists_with_no_input"] is False   # cut the drive -> the state runs away


# --- determinism ----------------------------------------------------------- #
def test_determinism_under_fixed_seed(systems):
    latch, _, _ = systems
    a = measure_C3_local_info(latch, CFG)
    b = measure_C3_local_info(latch, CFG)
    assert a["info_bits"] == b["info_bits"]
    c = measure_C4_persistence(latch, CFG)
    d = measure_C4_persistence(latch, CFG)
    assert c["memory_bits"] == d["memory_bits"]
    assert c["bias_pulse2_bits"] == d["bias_pulse2_bits"]


# --- zero-D / symmetric sanity --------------------------------------------- #
def test_zero_D_symmetric_no_preferred_well(systems):
    """At D=0 the latch has NO preferred well: from the symmetric point the
    outcome is pure noise (the genus includes random symmetry-breaking, which is
    NOT a steer). Over many trials the split is unbiased."""
    latch, _, _ = systems
    rng = np.random.default_rng(CFG.seed + 99)
    k = 400
    x0 = np.zeros(k)
    finals = settle(x0, latch, D=0.0, temp=CFG.temp, dt=CFG.dt,
                    n_steps=CFG.settle_steps, rng=rng)
    frac_pos = np.mean(finals > 0.0)
    assert abs(frac_pos - 0.5) < 0.1     # no directional bias supplied by D=0


def test_mutual_info_bounds():
    a = np.array([0, 1] * 500)                                        # exactly balanced -> H(a)=1 bit
    assert mutual_info_bits(a, a) == pytest.approx(1.0, abs=1e-9)     # identical -> 1 bit
    rng = np.random.default_rng(0)
    b = rng.integers(0, 2, size=1000)
    assert mutual_info_bits(a, b) < 0.05                             # independent -> ~0
