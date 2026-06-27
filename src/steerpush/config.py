"""Locked Step-5 parameters (pre-registered v0.0.2).

ASCII only. Every simulation/measure parameter lives here so it is logged with
every result (pre_registration.md Section 7.2: parameters and seeds recorded
with the run). Nothing here is observer-relative; all values are properties of
the system and its dynamics.

Matched-pair design (CLAUDE.md): the bistable latch and the monostable push
control differ in EXACTLY ONE feature -- the number of minima (multistability).
The monostable well stiffness is tuned to the bistable well curvature so the
local relaxation timescale is identical and the only difference is the second
minimum.
"""

from dataclasses import dataclass, asdict, field
from typing import Tuple


@dataclass(frozen=True)
class Config:
    # --- potential geometry ---
    well_sep: float = 1.0        # b: bistable minima at +/- b
    barrier: float = 1.0         # U0: bistable barrier height at x=0
    #   V_bistable(x)  = U0 * ((x/b)^2 - 1)^2   (minima at +/-b, value 0; barrier U0 at 0)
    #   curvature at each well V''(+/-b) = 8 U0 / b^2
    #   V_monostable(x) = 0.5 * kappa * x^2     (single minimum at 0)
    #   kappa is set to the bistable well curvature => identical local stiffness.
    # mono_stiffness is derived in CFG below so it always tracks (barrier, well_sep).
    mono_stiffness: float = 8.0  # kappa (overwritten in CFG to 8*U0/b^2)

    # --- noise / integration (overdamped Langevin, friction = 1) ---
    temp: float = 0.05           # T: barrier/T = 20 => spontaneous hopping negligible
    dt: float = 1.0e-3
    settle_steps: int = 10000    # t = 10 >> well relaxation time (~1/8)
    pulse_steps: int = 2000      # transient-pulse window (t = 2)
    hold_steps: int = 10000      # D=0 hold for the two-pulse memory test (t = 10)
    flux_steps: int = 200000     # long run for steady-state net-current estimate

    # --- differences D (additive bias force) ---
    d_sweep: Tuple[float, ...] = (1.0, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001)  # C2, toward 0
    d_subthreshold: float = 0.0  # C3 conditioning value: D supplies no directional bit
    d_pulse: float = 2.0         # C4 first-pulse magnitude: SUPER-critical (> spinodal
    #   |D_crit| = 4c(b/sqrt3)(b^2/3 - b^2)| = 16 U0/(3 sqrt3 b) ~= 1.54 here) so pulse-1
    #   reliably SETS the well; the trigger-smallness property is C2's job, not C4's.
    d_readout: float = 0.2       # C4 second-pulse readout difference (sub-threshold)

    # --- sampling ---
    n_ic: int = 201              # C1 initial conditions, spread over [-ic_range, ic_range]
    ic_range: float = 2.0
    n_trials: int = 400          # C3/C4 Monte-Carlo trials
    grid_n: int = 2001           # FEP / entropy stationary grid
    grid_range: float = 2.5

    # --- driven (A) decoy: maintenance-measure positive control (NOT a steer/push
    #     candidate). A periodic potential V=-cos(x) with a constant nonconservative
    #     drive f > 1 has no fixed point -> a nonequilibrium steady state with net
    #     current and POSITIVE entropy production: the (A) beneficiary/dissipative
    #     archetype. It exists only to show the (A)/(B) guard can read nonzero. ---
    drive_force: float = 1.5

    # --- operational readout thresholds (NOT the bar; the bar is Section 7.3) ---
    c2_divergence_ratio: float = 10.0   # gain(min D)/gain(max D) > this => "diverges"
    c2_well_scale_frac: float = 0.5     # |R(min D)| > frac*well_sep => outcome is full-size
    #   and D-independent (the LOCKED 7.2 definition: a vanishing trigger flips a FULL-size
    #   outcome). Gain divergence alone is non-specific (any sub-harmonic single well has it);
    #   trigger-not-drive requires divergence AND the outcome staying well-scale as D -> 0.
    info_high_bits: float = 0.5         # MI above => clearly > 0 (steer)
    info_low_bits: float = 0.1          # MI below => ~ 0 (push)
    rest_drift_tol: float = 1.0e-3      # |x_end - x_well| below => state persists with no input
    mode_window: float = 0.3            # FEP self-evidencing: stationary mass within this of a mode

    # --- seeds (deterministic) ---
    seed: int = 20260626

    def to_dict(self) -> dict:
        return asdict(self)


# Single locked instance, with mono_stiffness forced to the matched value.
CFG = Config(mono_stiffness=8.0 * Config().barrier / (Config().well_sep ** 2))
