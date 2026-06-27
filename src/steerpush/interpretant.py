"""Step 6 -- interpretant-proxy / surplus (misrepresentation) measure.

ASCII only. EXTENDS the Step-5 apparatus (does not rewrite it): reuses the
conceded bistable latch as the token source, the maintenance/Deacon measure (with
its driven-(A) control) for the beneficiary arm, and the FEP-flat machinery.

Surplus = aboutness operationalized as the possibility of MISREPRESENTATION
(Dretske, pre-reg 9.2): under FALSE-TOKEN INJECTION, does a SYSTEM-INTERNAL cost
variable treat a false token AS ERROR (keyed to correctness), rather than merely
taking a different causal trajectory? Memory has none; a sign does.

Non-circularity (9.5): the surplus estimator reads the differential of the
system's OWN viability variable v across correctness -- it is NOT the
maintenance-work measure -- so any surplus<->beneficiary link is a DISCOVERY, not
a definition.

Model. The read-out acts on the latched token b (= the latch's bit), producing an
action a = b. The world state w is the fact the token is about; a TRUE token has
b = w, a FALSE token (injected) has b = -w. The action is APT (world_fit = +1)
when a = w, INAPT (-1) when a = -w. A viability resource v leaks toward death (0)
and is REPLENISHED only by apt action, scaled by the feedback strength gamma:

    v_{t+1} = v_t + dt*(gamma*v_drive*apt - v_leak*v_t) + noise,   apt = max(world_fit, 0)

so the steady viability is gamma*v_drive/v_leak for apt (alive) and ~0 for inapt
(dead). gamma = 0 (INERT): the read-out acts but v is decoupled -- pure mechanism,
no beneficiary. gamma > 0 (SELF-MAINTAINING): apt use holds v far from equilibrium
(a beneficiary), inapt use lets it die.

Two correctness standards (9.2): S1 PERSISTENCE (correct = the apt action that
sustains the system; system-internal), S2 FIXED-TEMPLATE (correct = the action
matches a fixed EXTERNAL template; external, no feedback).
"""

import numpy as np

from .config import CFG
from .dynamics import make_bistable, make_monostable, make_featureless, make_driven_ring, settle
from .measures import measure_fep_flatness, measure_maintenance_work
from .battery import run_C_battery


# --------------------------------------------------------------------------- #
# shared surplus estimator
# --------------------------------------------------------------------------- #
def surplus_stat(correct, cost) -> float:
    """Surplus = |E[cost | correct] - E[cost | incorrect]|: the differential response
    of a SYSTEM-INTERNAL cost variable to correctness. > 0 only when a system-internal
    variable treats incorrect tokens as error. Shared by the read-out family and the
    positive control so the same estimator validates on a known error-corrector."""
    correct = np.asarray(correct, dtype=bool)
    cost = np.asarray(cost, dtype=float)
    if correct.all() or (~correct).all():
        return 0.0
    return float(abs(cost[correct].mean() - cost[~correct].mean()))


# --------------------------------------------------------------------------- #
# read-out family: false-token injection -> viability cost
# --------------------------------------------------------------------------- #
def _viability_steady(gamma, apt, cfg, rng):
    """Vectorized viability steady state. apt is an array in {0,1} (apt action or not).
    Returns the system's own viability v after v_steps (alive ~ gamma*v_drive/v_leak,
    dead ~ 0)."""
    n = apt.shape[0]
    v = np.zeros(n)
    sd = np.sqrt(2.0 * cfg.v_temp * cfg.dt)
    drive = gamma * cfg.v_drive * apt
    for _ in range(cfg.v_steps):
        v += cfg.dt * (drive - cfg.v_leak * v) + sd * rng.standard_normal(n)
    return v


def run_readout_trials(gamma, standard, cfg, rng):
    """One false-token-injection batch. Returns (correct_by_standard, cost=viability)."""
    n = cfg.n_surplus_trials
    w = rng.integers(0, 2, n) * 2 - 1                 # world fact in {-1,+1}
    false_token = rng.integers(0, 2, n).astype(bool)  # inject mismatch on half
    b = np.where(false_token, -w, w)                  # token (latched bit)
    a = b                                              # action follows the token
    world_fit = np.where(a == w, 1.0, -1.0)            # apt (true) vs inapt (false)
    apt = np.maximum(world_fit, 0.0)
    cost = _viability_steady(gamma, apt, cfg, rng)     # system-internal cost variable

    if standard == "S1":                               # persistence: apt sustains => correct
        correct = world_fit > 0
    elif standard == "S2":                             # match a fixed EXTERNAL template
        correct = a == np.sign(cfg.template_value)
    else:
        raise ValueError(standard)
    return correct, cost


def measure_surplus(gamma, standard, cfg=CFG):
    rng = np.random.default_rng(cfg.seed + 600 + (0 if standard == "S1" else 1) + int(round(gamma * 1000)))
    correct, cost = run_readout_trials(gamma, standard, cfg, rng)
    s = surplus_stat(correct, cost)
    return {"surplus": s, "surplus_positive": bool(s > cfg.surplus_thresh),
            "n_correct": int(np.sum(correct))}


# --------------------------------------------------------------------------- #
# family maintenance (Deacon arm) -- native far-from-equilibrium throughput
# --------------------------------------------------------------------------- #
def measure_family_maintenance(gamma, cfg=CFG):
    """Deacon arm, via the REUSED Step-5 maintenance measure (with its driven-(A)
    control) UNCHANGED. A self-maintaining read-out holds the system far from
    equilibrium exactly as the driven ring does, so its housekeeping-heat rate IS the
    ring's maintenance at drive proportional to the feedback strength gamma. gamma = 0
    -> drive 0 -> equilibrium -> entropy_production = 0 EXACTLY (Deacon-PUSH, (B));
    gamma > 0 -> running NESS -> entropy_production > 0, rising with gamma (Deacon-(A)).
    This is a genuine nonequilibrium throughput, and a DIFFERENT instrument from the
    surplus estimator (a viability-state differential) -- non-circularity (9.5)."""
    drive = gamma * cfg.maint_drive_scale
    m = measure_maintenance_work(make_driven_ring(), cfg, drive=drive)
    ep = m["entropy_production"]
    return {"entropy_production": ep, "deacon_push": bool(ep < cfg.maint_eps_step6),
            "net_current": m["net_current"], "drive": drive}


# --------------------------------------------------------------------------- #
# surplus POSITIVE CONTROL (9.5): an explicit error-corrector MUST read surplus > 0
# --------------------------------------------------------------------------- #
def run_positive_control(cfg=CFG):
    """A regulator with an internal set-point s*. 'token': true = undisturbed,
    false = a disturbance pushes the state off s*. The internal error e = s* - s is
    a cost/correction signal the controller acts on (s relaxes toward s*). Cost =
    mean |e| over the trial. False tokens are treated AS ERROR (large e, corrected);
    true tokens are not. The SAME surplus_stat must read > 0."""
    rng = np.random.default_rng(cfg.seed + 700)
    n = cfg.pc_trials
    false_token = rng.integers(0, 2, n).astype(bool)
    s = np.full(n, cfg.pc_setpoint, dtype=float)
    s = np.where(false_token, s + cfg.pc_perturb, s)   # false-token disturbance
    sd = np.sqrt(2.0 * cfg.v_temp * cfg.dt)
    err_acc = np.zeros(n)
    for _ in range(cfg.pc_steps):
        e = cfg.pc_setpoint - s
        s = s + cfg.dt * (cfg.pc_gain * (cfg.pc_setpoint - s)) + sd * rng.standard_normal(n)
        err_acc += np.abs(e)
    cost = err_acc / cfg.pc_steps                       # mean internal error magnitude
    correct = ~false_token                              # set-point standard: undisturbed = correct
    return correct, cost


def measure_positive_control(cfg=CFG):
    correct, cost = run_positive_control(cfg)
    s = surplus_stat(correct, cost)
    return {"surplus": s, "surplus_positive": bool(s > cfg.surplus_thresh)}


# --------------------------------------------------------------------------- #
# multistable EQUILIBRIUM error-store: the panel's live OCCUPY route
# --------------------------------------------------------------------------- #
def run_error_store(cfg, rng):
    """A SECOND bistable latch E that RECORDS token-correctness at equilibrium (zero
    throughput, Deacon-PUSH -- like the Step-5 latch). This is the panel's candidate
    for surplus>0 AND Deacon-PUSH WITHOUT a beneficiary: a token-dependent stationary
    distribution that an ergodic-mixing argument (for unimodal relaxers) does not
    exclude. It tests the load-bearing 9.2 distinction: RECORDING correctness ("merely
    a different causal trajectory") vs TREATING a false token AS ERROR.

    Returns (correct, raw_cost, persistence_cost):
      raw_cost = the recorded bit E -- differs maximally across correctness (it records).
      persistence_cost = the store's own death-exposure (1 - retention of E over a hold)
        -- the FUNCTIONAL cost: does the store persist-DIFFERENTIALLY on correct vs
        incorrect? An equilibrium bistable well holds EITHER bit equally, so retention is
        token-independent and this is ~0. Recording is not treating-as-error."""
    latch = make_bistable(cfg.well_sep, cfg.barrier)
    n = cfg.n_surplus_trials
    w = rng.integers(0, 2, n) * 2 - 1
    false_token = rng.integers(0, 2, n).astype(bool)
    b = np.where(false_token, -w, w)
    correct = b == w                                   # world-correctness of the token
    m = np.where(correct, 1.0, -1.0)                   # the comparison the store records

    # record m into the store (super-critical set), then let it hold at equilibrium
    x = np.zeros(n)
    x = settle(x, latch, D=m * cfg.d_pulse, temp=cfg.temp, dt=cfg.dt, n_steps=cfg.pulse_steps, rng=rng)
    x = settle(x, latch, D=0.0, temp=cfg.temp, dt=cfg.dt, n_steps=cfg.hold_steps, rng=rng)
    E = np.sign(x)
    raw_cost = E.astype(float)

    # persistence: retention of the recorded bit over a further equilibrium hold
    x2 = settle(x, latch, D=0.0, temp=cfg.temp, dt=cfg.dt, n_steps=cfg.hold_steps, rng=rng)
    retained = (np.sign(x2) == E).astype(float)
    persistence_cost = 1.0 - retained                  # death-exposure; ~0 and token-independent
    return correct, raw_cost, persistence_cost


def measure_error_store(cfg=CFG):
    rng = np.random.default_rng(cfg.seed + 800)
    correct, raw_cost, persistence_cost = run_error_store(cfg, rng)
    raw = surplus_stat(correct, raw_cost)              # ~2: RECORDS correctness (a correlate)
    functional = surplus_stat(correct, persistence_cost)  # ~0: does NOT treat-as-error
    latch = make_bistable(cfg.well_sep, cfg.barrier)
    mnt = measure_maintenance_work(latch, cfg, drive=0.0)
    deacon_push = bool(mnt["entropy_production"] < cfg.maint_eps_step6)
    return {
        "raw_surplus_records_correctness": raw,
        "functional_surplus_treats_as_error": functional,
        "surplus_positive_functional": bool(functional > cfg.surplus_thresh),
        "deacon_push": deacon_push,
        "would_occupy_under_RAW_correlate": bool(deacon_push and raw > cfg.surplus_thresh),
        "occupies_under_FUNCTIONAL": bool(deacon_push and functional > cfg.surplus_thresh),
    }


# --------------------------------------------------------------------------- #
# full Step-6 grid + bar
# --------------------------------------------------------------------------- #
def run_step6(cfg=CFG) -> dict:
    """gamma sweep x {S1, S2}. For each cell: C-readout (inherited STEER latch),
    FEP-flat (reused), Deacon arm (family maintenance), surplus. Plus the surplus
    positive control and the reused driven-(A) maintenance anchor."""
    # measure-validity first
    pc = measure_positive_control(cfg)
    # the panel's live OCCUPY route: an equilibrium multistable error-store
    store = measure_error_store(cfg)

    # C-readout + FEP-flat are inherited from the Step-5 latch (gamma-independent base)
    cbatt = run_C_battery(cfg)
    latch_steer = cbatt["bistable_latch"]["readout"]["verdict"] == "STEER"
    latch, mono, feat = make_bistable(cfg.well_sep, cfg.barrier), \
        make_monostable(cfg.mono_stiffness), make_featureless(cfg.mono_stiffness)
    fep = measure_fep_flatness((latch, mono, feat), cfg)
    fep_flat = bool(fep["verdict_constant"])

    # reused driven-(A) maintenance anchor (unchanged): proves the Deacon arm reads nonzero
    anchor = measure_maintenance_work(make_driven_ring(), cfg, drive=cfg.drive_force)

    grid = []
    for standard in ("S1", "S2"):
        for gamma in cfg.gamma_sweep:
            sur = measure_surplus(gamma, standard, cfg)
            mnt = measure_family_maintenance(gamma, cfg)
            occupied = bool(latch_steer and fep_flat and mnt["deacon_push"]
                            and sur["surplus_positive"])
            grid.append({
                "standard": standard, "gamma": gamma,
                "C_steer": bool(latch_steer), "fep_flat": fep_flat,
                "entropy_production": mnt["entropy_production"],
                "deacon_push": mnt["deacon_push"],
                "surplus": sur["surplus"], "surplus_positive": sur["surplus_positive"],
                "bar_occupied": occupied,
            })

    # the error-store occupies only if its FUNCTIONAL (treats-as-error) surplus clears the
    # bar with Deacon-PUSH -- recording correctness (raw) is not enough (9.2).
    store_occupies = bool(latch_steer and fep_flat and store["occupies_under_FUNCTIONAL"])

    return {
        "params": cfg.to_dict(),
        "positive_control": pc,
        "error_store": store,
        "maintenance_anchor_driven_A": {
            "entropy_production": anchor["entropy_production"],
            "deacon_push": bool(anchor["entropy_production"] < cfg.maint_eps_step6),
        },
        "latch_C_readout": "STEER" if latch_steer else "PUSH",
        "fep_flat": fep_flat,
        "grid": grid,
        "solution_set_occupied": bool(any(c["bar_occupied"] for c in grid) or store_occupies),
    }
