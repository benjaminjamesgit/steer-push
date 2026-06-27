"""Run the full Step-5 battery and dump every measured scalar.

ASCII only. Deterministic under the locked seeds in steerpush.config. Writes the
result to results/step5_result.json and prints a readable summary.

    python scripts/run_step5.py
"""

import json
import os

from steerpush.battery import run_battery
from steerpush.config import CFG


def main():
    res = run_battery(CFG)

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "step5_result.json")
    with open(out_path, "w") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)

    print("=" * 70)
    print("STEP 5 BATTERY -- bistable latch vs matched monostable push control")
    print("=" * 70)
    print("params:", json.dumps(res["params"], sort_keys=True))
    print()

    for name, blk in res["C"].items():
        rd = blk["readout"]
        print(f"[{name}]")
        print(f"  C1 multistability : n_basins={blk['C1']['n_basins']} "
              f"centers={[round(c,3) for c in blk['C1']['basin_centers']]}  steer={rd['C1_steer']}")
        c2 = blk["C2"]
        print(f"  C2 trigger/drive  : trigger_not_drive={c2['trigger_not_drive']} "
              f"(diverges={c2['diverges']} gain_ratio={c2['gain_ratio']:.3g} "
              f"R(minD)={c2['R_at_smallest_D']:.3g} well_scale={c2['outcome_well_scale']})  steer={rd['C2_steer']}")
        print(f"  C3 local-info     : I(R;prior|D)={blk['C3']['info_bits']:.3f} bits  steer={rd['C3_steer']}")
        c4 = blk["C4"]
        print(f"  C4 persistence    : memory={c4['memory_bits']:.3f} held={c4['held_fraction']:.3f} "
              f"bias_pulse2={c4['bias_pulse2_bits']:.3f} bits  steer={rd['C4_steer']}")
        print(f"  ==> C readout     : {rd['verdict']}")
        print()

    fep = res["FEP"]
    print("[FEP-flatness]")
    for r in fep["records"]:
        print(f"  {r['name']:>22}: n_modes={r['n_modes']} self_evidencing={r['self_evidencing']} "
              f"mean_surprisal={r['mean_surprisal_nats']:.3f} nats")
    print(f"  verdict_constant={fep['verdict_constant']}  n_modes={fep['n_modes_by_system']}  "
          f"surprisal_varies={fep['mean_surprisal_varies']}")
    print(f"  escape hatch: fep_can_track_split={fep['fep_can_track_split']} "
          f"(latch surprisal {fep['latch_surprisal']:.3f} vs wide-PUSH-probe {fep['probe_kappa1_push_surprisal']:.3f})")
    print(f"  only robust separator: {fep['only_robust_separator']}")
    print()

    print("[maintenance / Deacon-PUSH]  (driven_ring_A = (A) positive control)")
    for name, m in res["maintenance"].items():
        print(f"  {name:>22}: drift_at_rest={m['drift_at_rest']:.2e} "
              f"net_current={m['net_current']:.3e} entropy_prod={m['entropy_production']:.3e} "
              f"persists_no_input={m['persists_with_no_input']}")
    print()
    print(f"result written to {out_path}")


if __name__ == "__main__":
    main()
