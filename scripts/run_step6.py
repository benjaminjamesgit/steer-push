"""Run the full Step-6 interpretant-proxy grid and dump every scalar.

ASCII only. Deterministic under the locked seeds in steerpush.config. Writes
results/step6_result.json and prints a readable summary.

    python scripts/run_step6.py
"""

import json
import os

from steerpush.config import CFG
from steerpush.interpretant import run_step6


def main():
    res = run_step6(CFG)

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "step6_result.json")
    with open(out_path, "w") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)

    print("=" * 74)
    print("STEP 6 -- interpretant-proxy close-or-occupy (surplus = misrepresentation)")
    print("=" * 74)
    pc = res["positive_control"]
    print(f"[surplus positive control] surplus={pc['surplus']:.3f}  positive={pc['surplus_positive']}  "
          f"(must be > 0 or the measure is broken)")
    st = res["error_store"]
    print(f"[multistable equilibrium error-store] (panel's live OCCUPY route)")
    print(f"    raw surplus (RECORDS correctness)        = {st['raw_surplus_records_correctness']:.3f}  "
          f"-> would_occupy_under_RAW_correlate={st['would_occupy_under_RAW_correlate']}")
    print(f"    functional surplus (TREATS AS ERROR)     = {st['functional_surplus_treats_as_error']:.3f}  "
          f"deacon_push={st['deacon_push']}  occupies_under_FUNCTIONAL={st['occupies_under_FUNCTIONAL']}")
    anc = res["maintenance_anchor_driven_A"]
    print(f"[Deacon (A) anchor: driven ring] entropy_production={anc['entropy_production']:.3f}  "
          f"deacon_push={anc['deacon_push']}  (reused Step-5 measure, unchanged)")
    print(f"[latch base] C-readout={res['latch_C_readout']}  FEP-flat={res['fep_flat']}")
    print()
    print(f"  {'std':>3} {'gamma':>5} | {'C':>5} {'FEP':>4} | {'entropy_prod':>12} {'Deacon-PUSH':>11} | "
          f"{'surplus':>8} {'surplus>0':>9} | {'BAR OCCUPIED':>12}")
    print("  " + "-" * 86)
    for c in res["grid"]:
        print(f"  {c['standard']:>3} {c['gamma']:>5.2f} | "
              f"{'STEER' if c['C_steer'] else 'push':>5} {str(c['fep_flat']):>4} | "
              f"{c['entropy_production']:>12.4f} {str(c['deacon_push']):>11} | "
              f"{c['surplus']:>8.3f} {str(c['surplus_positive']):>9} | {str(c['bar_occupied']):>12}")
    print()
    print(f"SOLUTION SET OCCUPIED (any cell STEER & FEP-flat & Deacon-PUSH & surplus>0): "
          f"{res['solution_set_occupied']}")
    print(f"=> {'OCCUPY (CONTRIBUTION)' if res['solution_set_occupied'] else 'EMPTY -> deflationary CLOSE'}")
    print()
    print(f"result written to {out_path}")


if __name__ == "__main__":
    main()
