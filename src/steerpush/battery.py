"""Assemble the {latch, monostable, featureless} battery and run every measure.

ASCII only. Produces a single results dict with all measured scalars plus the
OPERATIONAL steer/push readout per system (the bar in Section 7.3 is applied in
the adjudication, not here).
"""

import numpy as np

from .config import CFG
from .dynamics import make_bistable, make_monostable, make_featureless, make_driven_ring
from .measures import (
    measure_C1_multistability,
    measure_C2_gain,
    measure_C3_local_info,
    measure_C4_persistence,
    measure_fep_flatness,
    measure_maintenance_work,
)


def build_systems(cfg=CFG):
    latch = make_bistable(cfg.well_sep, cfg.barrier)
    mono = make_monostable(cfg.mono_stiffness)
    featureless = make_featureless(cfg.mono_stiffness)
    return latch, mono, featureless


def _c_readout(cfg, c1, c2, c3, c4) -> dict:
    """Operational C verdict from the four sub-measures (Section 7.2 thresholds)."""
    c1_steer = c1["n_basins"] >= 2
    c2_steer = c2["trigger_not_drive"]
    c3_steer = c3["info_bits"] > cfg.info_high_bits
    c4_steer = c4["memory_bits"] > cfg.info_high_bits
    all_steer = c1_steer and c2_steer and c3_steer and c4_steer
    return {
        "C1_steer": bool(c1_steer),
        "C2_steer": bool(c2_steer),
        "C3_steer": bool(c3_steer),
        "C4_steer": bool(c4_steer),
        "verdict": "STEER" if all_steer else "PUSH",
    }


def run_C_battery(cfg=CFG) -> dict:
    """C1-C4 on the matched pair (latch, monostable)."""
    latch, mono, _ = build_systems(cfg)
    out = {}
    for sys in (latch, mono):
        c1 = measure_C1_multistability(sys, cfg)
        c2 = measure_C2_gain(sys, cfg)
        c3 = measure_C3_local_info(sys, cfg)
        c4 = measure_C4_persistence(sys, cfg)
        out[sys.name] = {
            "C1": c1, "C2": c2, "C3": c3, "C4": c4,
            "readout": _c_readout(cfg, c1, c2, c3, c4),
        }
    return out


def run_battery(cfg=CFG) -> dict:
    """Full Step-5 battery: C measures (matched pair) + FEP-flatness + maintenance
    (all three systems)."""
    latch, mono, featureless = build_systems(cfg)
    c = run_C_battery(cfg)
    fep = measure_fep_flatness((latch, mono, featureless), cfg)
    maintenance = {
        s.name: measure_maintenance_work(s, cfg) for s in (latch, mono, featureless)
    }
    # positive control: a driven nonequilibrium (A) system MUST read positive maintenance,
    # proving the (A)/(B) guard discriminates rather than returning 0 by construction.
    decoy = make_driven_ring()
    maintenance[decoy.name] = measure_maintenance_work(decoy, cfg, drive=cfg.drive_force)
    return {
        "params": cfg.to_dict(),
        "C": c,
        "FEP": fep,
        "maintenance": maintenance,
    }
