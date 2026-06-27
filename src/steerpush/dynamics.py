"""Overdamped Langevin dynamics for the steer/push battery.

ASCII only. Pure functions of the system's own state; no observer, no
interpreter, no beneficiary.

    dx = (-V'(x) + D) dt + sqrt(2 T) dW            (friction = 1)

Euler-Maruyama integration. D is an additive bias force (the "difference"),
applied over a window and then removed. The three systems:

    bistable_latch       V(x) = U0 * ((x/b)^2 - 1)^2     (two minima: the (B) candidate)
    monostable_push      V(x) = 0.5 * kappa * x^2        (one minimum: matched control)
    featureless_persister  same single-well V, used with NO D-structure (FEP battery only)
"""

import numpy as np
from dataclasses import dataclass
from typing import Callable, Tuple


@dataclass(frozen=True)
class System:
    name: str
    V: Callable[[np.ndarray], np.ndarray]    # potential
    dV: Callable[[np.ndarray], np.ndarray]   # V'(x), the gradient force is -dV
    minima: Tuple[float, ...]                # known minima (for labeling/reference)


def make_bistable(b: float, u0: float) -> System:
    c = u0 / (b ** 4)                        # V = c (x^2 - b^2)^2 = U0 ((x/b)^2 - 1)^2
    def V(x):
        x = np.asarray(x, dtype=float)
        return c * (x * x - b * b) ** 2
    def dV(x):
        x = np.asarray(x, dtype=float)
        return 4.0 * c * x * (x * x - b * b)
    return System("bistable_latch", V, dV, (-b, b))


def make_monostable(kappa: float) -> System:
    def V(x):
        x = np.asarray(x, dtype=float)
        return 0.5 * kappa * x * x
    def dV(x):
        x = np.asarray(x, dtype=float)
        return kappa * x
    return System("monostable_push", V, dV, (0.0,))


def make_featureless(kappa: float) -> System:
    # Same single-well potential as the monostable control; distinguished only by
    # how it is used (no D-structure) -- a bare persister relaxing to one fixed point.
    s = make_monostable(kappa)
    return System("featureless_persister", s.V, s.dV, (0.0,))


def make_driven_ring() -> System:
    # Periodic potential V(x) = -cos(x). Run with a CONSTANT nonconservative drive
    # f (passed as an always-on D to the maintenance measure): for f > 1 there is no
    # fixed point, so the steady state carries a net current and dissipates a positive
    # housekeeping heat -- the (A) dissipative/"beneficiary" archetype. This is NOT a
    # steer/push candidate; it is the positive control proving the (A)/(B) maintenance
    # guard can read nonzero (it is not zero-by-construction for everything).
    def V(x):
        x = np.asarray(x, dtype=float)
        return -np.cos(x)
    def dV(x):
        x = np.asarray(x, dtype=float)
        return np.sin(x)
    return System("driven_ring_A", V, dV, (0.0,))


def step(x, system: System, D, temp: float, dt: float, rng) -> np.ndarray:
    """One Euler-Maruyama step. D and x broadcast; temp == 0 is deterministic."""
    x = np.asarray(x, dtype=float)
    force = -system.dV(x) + D
    x_new = x + force * dt
    if temp != 0.0:
        x_new = x_new + np.sqrt(2.0 * temp * dt) * rng.standard_normal(np.shape(x))
    return x_new


def settle(x0, system: System, D, temp: float, dt: float, n_steps: int, rng) -> np.ndarray:
    """Integrate for n_steps and return the final state (the retained state R)."""
    x = np.array(x0, dtype=float)
    for _ in range(n_steps):
        x = step(x, system, D, temp, dt, rng)
    return x


def trajectory(x0, system: System, D, temp: float, dt: float, n_steps: int, rng) -> np.ndarray:
    """Integrate and return the full scalar trajectory (x0 must be scalar)."""
    x = float(x0)
    out = np.empty(n_steps + 1, dtype=float)
    out[0] = x
    for i in range(n_steps):
        x = float(step(np.asarray(x), system, D, temp, dt, rng))
        out[i + 1] = x
    return out
