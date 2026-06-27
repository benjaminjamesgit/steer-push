"""steerpush -- toy dynamical-systems battery for the steer-vs-push criterion.

See pre_registration.md (sections 0-7 locked) for the criterion, the bar, and
the Step-5 predicted verdicts. Nothing in this package presupposes an observer,
an interpreter, or a beneficiary; the FEP measure imports the competitor's
construct only to test flatness.
"""

from .config import CFG, Config
from .battery import build_systems, run_battery, run_C_battery

__all__ = ["CFG", "Config", "build_systems", "run_battery", "run_C_battery"]
