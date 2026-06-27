# steer-push

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20947370.svg)](https://doi.org/10.5281/zenodo.20947370)

**An empirical program testing whether a physical difference can be a *sign* rather than a *cause* below life — and a record of how it closed that question deflationarily.**

steer-push is the pre-life test arm of a naturalist/physical-semiotics question. It builds an operational criterion `C(D, S, dyn)` for when a physical difference *steers* a system (selection) versus merely *pushes* it (causation), and asks, under pre-registration with predicted verdicts locked before each run:

> Can the steer/push distinction be drawn **below life** — with no chooser, no self-maintaining beneficiary, and no observer?

**Result (v0.2.x, terminal): No — and, for the reason that matters, necessarily.** The criterion cleanly separates multistable memory from monostable relaxation — a real, matched-pair distinction that Friston's free-energy principle and Deacon's teleodynamics do not draw. But that is *memory from relaxation*, not *sign from cause*. The surplus that would separate a sign from a recorded-cause-plus-memory — the possibility of misrepresentation — cannot be positive below life without re-importing the beneficiary/function the pre-life setting excludes. "A sign with no interpreter" is ill-posed at this level, not merely unconfirmed.

The full pre-registered lab notebook is [`pre_registration.md`](pre_registration.md); working conventions are in [`CLAUDE.md`](CLAUDE.md).

## What was built

`C(D, S, dyn)` takes a physical difference `D = {d, d'}` acting on a bare dynamical system `S` (a state space plus an evolution rule — no boundary, no self-maintenance, no observer) and grades whether `D` steers or pushes, read off the **retained state** `R` (the attractor `S` settles into).

- **Positive core.** A *push* supplies the outcome (response scales with `D`; `D -> 0` implies response `-> 0`). A *steer* selects among outcomes `S` already affords: it needs **afforded alternatives** (multistability) and must be a **trigger, not a drive** (a vanishing `D` still flips the outcome — the magnitude is the system's, not `D`'s).
- **Genus and species.** A *choice* is chooser-free — an irreversible **local creation of information**; the genus includes pure noise. The *species* — a sign — is a choice whose bit is **reliably coupled** to the difference, reliability sourced in the **persistence of the selector** ("memory without a mind").
- **Surplus = misrepresentation.** A sign must be able to **misrepresent** — say "D" when `D` did not obtain, with the falsity mattering to the system itself (Dretske). This is the measure the early criterion lacked.
- **The adversarial bar** (fixed before each run): a candidate counts only if it reads **STEER** and **FEP-flat** (Friston's description cannot separate it from a mere persister) and **Deacon-PUSH** (zero maintenance work — no beneficiary) and **surplus > 0**. If none does, concede (renaming).

## The arc — tested → found

| step | test | outcome |
|---|---|---|
| Step 5 (v0.1.x) | a bistable-latch STEER candidate vs. a matched monostable PUSH control | **CONCEDE (renaming)** — passes the operational gate, but the four measures collapse to one feature (multistability) and none detects *aboutness*. The latch is a flip-flop; the "sign" is bistable memory. |
| Step 6 (v0.2.x) | an interpretant-proxy family (a downstream read-out over feedback axis γ) + surplus = misrepresentation under two standards (persistence, fixed-template) + a multistable equilibrium error-store | **CLOSE (deflationary terminus)** — the full bar `STEER ∧ FEP-flat ∧ Deacon-PUSH ∧ surplus > 0` has an **empty solution set**; surplus is positive only where a beneficiary is present. |

## The result — the terminal close

Below life, with no interpretant, **misrepresentation has nowhere to live** — and misrepresentation is what separates a sign from a cause-plus-memory. The wall is the philosophy of content's own, re-derived below life:

1. **Informational content cannot misrepresent** (the disjunction problem; Dretske, Fodor). A "false" token is just a token caused by something other than `D`, so informationally it is *about whatever caused it*, never false. The *raw* surplus — a correlate that merely records the bit — is exactly this: the error-store records correctness (raw 2.0) yet cannot treat a false token *as error*.
2. **Teleo-content can misrepresent, but needs a function** (teleosemantics; Millikan). A token with the *function* of indicating `D` malfunctions when `D` is absent. The *functional* surplus — a cost the system itself acts on — reads `> 0` only when the read-out's correct use serves the system's own persistence: a **beneficiary**.

So **surplus and the no-beneficiary constraint are mutually exclusive.** Both sources of function close: *current self-maintenance* (a synchronic beneficiary — demonstrated across the γ-family and both standards) and *selection history* (etiological proper function — argued: normative selection requires historical beneficiaries, while beneficiary-free "selection" in the assembly-theory sense disclaims normativity and grounds no misrepresentation). The precise statement is in `pre_registration.md` §11.

## What holds, what closed

**Holds.** The criterion as a clean, observer-free separation of **multistable memory from monostable relaxation** — a real matched-pair distinction FEP and Deacon do not draw; the apparatus (latch dynamics; the FEP-flat and maintenance/Deacon arms with positive controls); the pre-registration discipline.

**Closed.** **Sign below life.** The criterion separates memory from relaxation, not sign from cause; "a sign with no interpreter" is ill-posed in the precise sense that the surplus distinguishing it cannot be positive without the beneficiary/function the pre-life setting excludes.

## Honest scope

A **theory-led close + exhaustion**, not a finite-scale empirical surprise. The Step-6 grid's mutual-exclusion is near-analytic (surplus and maintenance co-flow from one coupling, which *is* the thesis); its genuine empirical content is the two arms that *could* have dissociated and did not — the fixed-template standard at full maintenance, and the multistable equilibrium store. Demonstrated for **synchronic** architectures, **argued** for the **diachronic / selection-history** route via the assembly-theory fork; scoped to this family + two standards + the store, generalized by the teleosemantic argument — **not** a theorem over all conceivable pre-life systems. Vulnerable-in-the-right-way, like the program's earlier closes (Step 5; CIT).

## Why the close is trustworthy

Every step was **pre-registered** with predicted verdicts and the bar committed and pushed **before any number existed** (the HARD STOP is in the git history); the record is **append-only**; a **five-lens adversarial panel** reproduced every number bit-exactly, caught the one live OCCUPY route (the error-store) and three apparatus defects, all fixed **before** adjudication without moving a prediction or the bar. Confounds and amendments are in [`pre_registration.md`](pre_registration.md), not smoothed away.

## Scope (what is out)

steer-push is the **operational** arm only. The framework's value as a unifying lens, and its semiotic/applied readings, are not operational claims and are out of scope — neither verified nor closed. What is settled is narrow: *as an operational criterion below life, steer/push separates memory from relaxation, not sign from cause.*

## Repo map

- [`pre_registration.md`](pre_registration.md) — the pre-registered lab notebook (objects, bar, every step, result, panel, the §11 terminus; append-only).
- `src/steerpush/` — the apparatus. `scripts/` — run drivers. `results/` — recorded scalars. `tests/` — unit + property tests.

## Quick start

```bash
git clone https://github.com/benjaminjamesgit/steer-push.git
cd steer-push
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## References

Engaged, and re-derived below life: Dretske (*Knowledge and the Flow of Information*; *Misrepresentation*) and Fodor (*Psychosemantics*) — the disjunction problem; Millikan (*Language, Thought, and Other Biological Categories*) — etiological proper function. Tested against: Friston (free-energy principle), Deacon (*Incomplete Nature*, teleodynamics), Walker & Cronin (assembly theory).

## License

Apache License, Version 2.0. See [LICENSE](LICENSE).

## Citation

See [`CITATION.cff`](CITATION.cff).
