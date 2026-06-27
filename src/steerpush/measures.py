"""The C-STEER measures (C1-C4), the FEP-flatness check, and the Deacon /
maintenance-work check.

ASCII only. Every C measure is computed from the system's own states and
dynamics -- no observer, no interpreter, no presupposed code. The FEP measure
DELIBERATELY invokes the competitor's construct (Markov blanket / variational
free energy) in order to test flatness, and states that construction; this is
the one place the pre-registration licenses importing a competitor's framework.

The booleans returned here are OPERATIONAL readouts at the thresholds in
config.Config. They are NOT the bar; the bar is pre_registration.md Section 7.3
and is applied in the adjudication, not here.
"""

import numpy as np

from .dynamics import System, settle, trajectory


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def mutual_info_bits(a, b) -> float:
    """Empirical mutual information (bits) between two discrete-labeled arrays."""
    a = np.asarray(a)
    b = np.asarray(b)
    n = len(a)
    mi = 0.0
    for av in np.unique(a):
        pa = np.mean(a == av)
        for bv in np.unique(b):
            pb = np.mean(b == bv)
            pab = np.mean((a == av) & (b == bv))
            if pab > 0.0:
                mi += pab * np.log2(pab / (pa * pb))
    return float(max(mi, 0.0))


def _cluster_1d(values, tol: float):
    """Greedy 1D clustering: a gap > tol starts a new cluster. Returns centers."""
    order = np.sort(np.asarray(values, dtype=float))
    clusters = [[order[0]]]
    for f in order[1:]:
        if f - clusters[-1][-1] > tol:
            clusters.append([f])
        else:
            clusters[-1].append(f)
    return [float(np.mean(c)) for c in clusters]


def _logsumexp(v):
    m = np.max(v)
    return m + np.log(np.sum(np.exp(v - m)))


def _stable_centers(system, centers, h: float = 1e-4):
    """Keep only STABLE fixed points (attractors): V''(c) > 0, estimated as the
    slope of V'(x) through the center. An IC landing exactly on an unstable fixed
    point (a repeller, measure zero) is not a retained state -- any perturbation
    leaves it -- so it is not counted as a basin. Property of V; observer-free."""
    keep = []
    for c in centers:
        slope = (system.dV(c + h) - system.dV(c - h)) / (2.0 * h)
        if slope > 0.0:
            keep.append(c)
    return keep


# --------------------------------------------------------------------------- #
# C1 -- multistability (afforded alternatives)
# --------------------------------------------------------------------------- #
def measure_C1_multistability(system: System, cfg, tol: float = 0.05) -> dict:
    """Number of retained states under D=0 from many initial conditions.

    Deterministic (T=0): the basins of attraction are a property of V alone.
    Steer >= 2 (afforded alternatives); push = 1.
    """
    rng = np.random.default_rng(cfg.seed)
    x0 = np.linspace(-cfg.ic_range, cfg.ic_range, cfg.n_ic)
    finals = settle(x0, system, D=0.0, temp=0.0, dt=cfg.dt, n_steps=cfg.settle_steps, rng=rng)
    centers = _cluster_1d(finals, tol)
    stable = _stable_centers(system, centers)
    return {"n_basins": len(stable), "basin_centers": stable, "all_settled_centers": centers}


# --------------------------------------------------------------------------- #
# C2 -- trigger-not-drive (gain |dR|/|dD| as D -> 0)
# --------------------------------------------------------------------------- #
def measure_C2_gain(system: System, cfg) -> dict:
    """Retained state R under a STANDING bias D, from the symmetric start x0=0.

    Steer: a vanishing D still flips a full-size outcome, so |R|/|D| diverges as
    D -> 0. Push: R = D/kappa, gain finite and R -> baseline (0) as D -> 0.
    """
    rng = np.random.default_rng(cfg.seed)
    rows = []
    for D in cfg.d_sweep:
        R = float(settle(0.0, system, D=D, temp=0.0, dt=cfg.dt, n_steps=cfg.settle_steps, rng=rng))
        rows.append({"D": D, "R": R, "gain": abs(R) / abs(D)})
    gains = [r["gain"] for r in rows]
    diverges = gains[-1] > cfg.c2_divergence_ratio * gains[0]
    r_min = rows[-1]["R"]
    # Gain divergence alone is non-specific: |R|/|D| grows for ANY single well whose
    # response is sublinear near the origin (e.g. V ~ x^4). The LOCKED 7.2 signature is
    # stronger -- the retained outcome stays FULL-SIZE and D-independent as D -> 0 (the
    # well's magnitude, not D's). Require both.
    outcome_well_scale = abs(r_min) > cfg.c2_well_scale_frac * cfg.well_sep
    return {
        "rows": rows,
        "diverges": bool(diverges),
        "gain_ratio": float(gains[-1] / gains[0]),
        "R_at_smallest_D": r_min,
        "outcome_well_scale": bool(outcome_well_scale),
        "trigger_not_drive": bool(diverges and outcome_well_scale),
    }


# --------------------------------------------------------------------------- #
# C3 -- local information creation: I(R ; prior internal state | D)
# --------------------------------------------------------------------------- #
def measure_C3_local_info(system: System, cfg) -> dict:
    """Does the retained state carry a bit NOT supplied by D?

    Conditioning on a sub-threshold D (default 0: D supplies no directional bit),
    vary the system's PRIOR internal configuration (which afforded state it starts
    in, +/- b) and measure whether R depends on it.

    Steer: R = prior (the latch co-determines R) -> I > 0.
    Push:  R = f(D) only; the prior washes out -> I ~ 0.
    """
    rng = np.random.default_rng(cfg.seed + 1)
    k = cfg.n_trials
    prior = rng.integers(0, 2, size=k)                       # 0 -> -b, 1 -> +b
    x0 = np.where(prior == 1, cfg.well_sep, -cfg.well_sep).astype(float)
    finals = settle(x0, system, D=cfg.d_subthreshold, temp=cfg.temp,
                    dt=cfg.dt, n_steps=cfg.settle_steps, rng=rng)
    r_bit = (finals > 0.0).astype(int)
    mi = mutual_info_bits(prior, r_bit)
    return {"info_bits": mi, "conditioning_D": cfg.d_subthreshold}


# --------------------------------------------------------------------------- #
# C4 -- selector-persistence (two-pulse recursion / reliability)
# --------------------------------------------------------------------------- #
def measure_C4_persistence(system: System, cfg) -> dict:
    """Two-pulse protocol: apply d (pulse 1), REMOVE it (D=0 hold), then apply a
    second difference (pulse 2). Does pulse 1 reliably bias pulse 2 with the
    first D gone?

    Steer: the set bit survives the D=0 hold (memory) and conditions pulse 2.
    Push:  the state relaxes back during the hold; pulse 2 is f(D2) only.
    """
    rng = np.random.default_rng(cfg.seed + 2)
    k = cfg.n_trials
    p1 = rng.integers(0, 2, size=k)                          # pulse-1 sign bit
    d1 = np.where(p1 == 1, cfg.d_pulse, -cfg.d_pulse).astype(float)

    x = np.zeros(k)
    x = settle(x, system, D=d1, temp=cfg.temp, dt=cfg.dt, n_steps=cfg.pulse_steps, rng=rng)
    sign_after_pulse = np.sign(x)
    # remove D, hold
    x = settle(x, system, D=0.0, temp=cfg.temp, dt=cfg.dt, n_steps=cfg.hold_steps, rng=rng)
    s_mid = (x > 0.0).astype(int)
    memory_bits = mutual_info_bits(p1, s_mid)
    held_fraction = float(np.mean(np.sign(x) == sign_after_pulse))
    # pulse 2: a common readout difference applied to all trials
    x2 = settle(x, system, D=cfg.d_readout, temp=cfg.temp, dt=cfg.dt, n_steps=cfg.pulse_steps, rng=rng)
    r2_bit = (x2 > 0.0).astype(int)
    bias_pulse2_bits = mutual_info_bits(p1, r2_bit)
    return {
        "memory_bits": memory_bits,
        "held_fraction": held_fraction,
        "bias_pulse2_bits": bias_pulse2_bits,
    }


# --------------------------------------------------------------------------- #
# FEP-flatness (competitor check)
# --------------------------------------------------------------------------- #
def measure_fep_single(system: System, cfg) -> dict:
    """Standard FEP description of one system.

    Markov-blanket partition: a 1D overdamped particle admits NO nontrivial
    internal/blanket/external partition (you need >=3 coupled sub-state-spaces).
    So the FEP description reduces to its minimal, undisputed core: the system
    relaxes to the modes of its stationary (Boltzmann) density
        p*(x) proportional to exp(-V(x)/T),
    and thereby minimizes steady-state surprisal / variational free energy
        F = < -log p*(x) >.
    The "self-evidencing free-energy-minimizing persister" verdict is therefore
    TRUE for any gradient relaxer -- this is the tautology the FEP runs below
    life by construction.
    """
    x = np.linspace(-cfg.grid_range, cfg.grid_range, cfg.grid_n)
    logp = -system.V(x) / cfg.temp
    logp = logp - _logsumexp(logp)
    p = np.exp(logp)
    interior = p[1:-1]
    n_modes = int(np.sum((interior > p[:-2]) & (interior > p[2:])))
    mean_surprisal = float(np.sum(p * (-logp)))
    # self-evidencing (COMPUTED, not asserted): does the stationary mass concentrate
    # near the modes (minima) of p*? True for any gradient relaxer; would be False for a
    # flat/diffusive density. Computing it (rather than hardcoding True) keeps the
    # flatness verdict in principle falsifiable.
    mode_mass = float(sum(np.sum(p[np.abs(x - m) < cfg.mode_window]) for m in system.minima))
    return {
        "name": system.name,
        "n_modes": n_modes,
        "mean_surprisal_nats": mean_surprisal,
        "mode_mass": mode_mass,
        "self_evidencing": bool(mode_mass > 0.5),
    }


def measure_fep_flatness(systems, cfg) -> dict:
    """FEP-flat iff the FEP VERDICT is constant across the whole battery.

    Reports the per-system records, the flatness verdict, and -- conservatively
    -- the only quantity that DOES vary within the FEP description (the number
    of modes of p*), which is exactly C1 multistability re-expressed. If FEP
    "separates" steer from push only via n_modes, it does so by importing our
    criterion, not on its own self-evidencing terms.
    """
    records = [measure_fep_single(s, cfg) for s in systems]
    verdicts = set(r["self_evidencing"] for r in records)
    n_modes = [r["n_modes"] for r in records]
    surprisals = [r["mean_surprisal_nats"] for r in records]

    # Escape hatch (pre-reg 7.2: "if the construction can be made to track the steer/push
    # split, report that -- candidate FAILS"). Test the ONE native FEP scalar that is not
    # just a restatement of multimodality: the mean surprisal F = <-log p*>. If a PUSH
    # system can have HIGHER surprisal than the STEER latch, surprisal orders by well WIDTH,
    # not by steer/push -> it is not a robust separator. Probe with a wide monostable
    # (kappa=1.0). The bimodality separators (n_modes, the variational gap) ARE C1.
    x = np.linspace(-cfg.grid_range, cfg.grid_range, cfg.grid_n)

    def _surprisal(vfunc):
        lp = -vfunc(x) / cfg.temp
        lp = lp - _logsumexp(lp)
        return float(np.sum(np.exp(lp) * (-lp)))

    latch_surprisal = records[0]["mean_surprisal_nats"]
    probe_surprisal = _surprisal(lambda z: 0.5 * 1.0 * z * z)   # wide PUSH well, kappa=1.0
    # FEP tracks the split only if a PUSH system reliably reads LOWER on this scalar than
    # the STEER latch. The wide-well probe (a PUSH) reads higher -> it cannot.
    fep_can_track_split = bool(probe_surprisal < latch_surprisal)

    return {
        "records": records,
        "verdict_constant": len(verdicts) == 1,
        "n_modes_by_system": n_modes,
        "mean_surprisal_by_system": surprisals,
        "mean_surprisal_varies": bool(len({round(s, 6) for s in surprisals}) > 1),
        "latch_surprisal": latch_surprisal,
        "probe_kappa1_push_surprisal": probe_surprisal,
        "fep_can_track_split": fep_can_track_split,
        "only_robust_separator": "n_modes (= C1 multistability); mean surprisal also varies "
                                 "but tracks well-width, not steer/push",
    }


# --------------------------------------------------------------------------- #
# Deacon-PUSH / no-beneficiary (maintenance work; also the (A)/(B) guard)
# --------------------------------------------------------------------------- #
def measure_maintenance_work(system: System, cfg, drive: float = 0.0) -> dict:
    """Steady-state work required to HOLD the retained state.

    `drive` is an always-on nonconservative force (0 for the equilibrium steer/push
    systems; > 0 for the driven (A) decoy positive control).

    (1) Cut-driving test (T=0): start at a retained well, integrate; the drift away
        from it measures the input needed to keep the state. ~0 => the state persists
        with no input (equilibrium; no beneficiary).
    (2) Steady-state current at T>0: the mean drift velocity (net_current) and the
        housekeeping-heat rate entropy_production = |drive * net_current| / T. For a
        1D gradient (equilibrium) system detailed balance forces net_current ~ 0 and
        entropy_production = 0. A driven NESS reads both POSITIVE.

    ~0 => Deacon-PUSH (no maintenance, no beneficiary, (B)). Positive => the structure
    must dissipate to hold itself up ((A) in disguise).
    """
    rng = np.random.default_rng(cfg.seed + 3)
    x_well = float(system.minima[-1])
    x_end = float(settle(x_well, system, D=drive, temp=0.0, dt=cfg.dt,
                         n_steps=cfg.settle_steps, rng=rng))
    drift_at_rest = abs(x_end - x_well)

    traj = trajectory(x_well, system, D=drive, temp=cfg.temp, dt=cfg.dt,
                      n_steps=cfg.flux_steps, rng=rng)
    total_time = cfg.flux_steps * cfg.dt
    net_current = float((traj[-1] - traj[0]) / total_time)   # mean drift velocity ~ NESS current
    entropy_production = float(abs(drive * net_current) / cfg.temp)
    return {
        "drift_at_rest": drift_at_rest,
        "net_current": net_current,                  # ~0 at equilibrium (no housekeeping heat)
        "entropy_production": entropy_production,     # 0 at equilibrium; > 0 for a driven NESS
        "persists_with_no_input": bool(drift_at_rest < cfg.rest_drift_tol),
    }
