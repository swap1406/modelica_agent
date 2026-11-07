"""Readable units for any signal of any model.

Simulation results are stored in SI units (m/s, rad/s, J, W, K). Engineers read
km/h, rpm, kWh, kW and °C. This module converts values for display, chosen by the
signal's unit, so it works for every model. A model's glossary can ask for a
different display unit for a specific signal (e.g. a 0–1 fraction shown as %).
"""

from __future__ import annotations

# (from unit, to unit) → (factor, offset):  shown = raw × factor + offset
CONVERSIONS = {
    ("m/s", "km/h"): (3.6, 0.0),
    ("rad/s", "rpm"): (60 / 6.283185307179586, 0.0),
    ("J", "kWh"): (1 / 3.6e6, 0.0),
    ("J", "Wh"): (1 / 3600, 0.0),
    ("W", "kW"): (1e-3, 0.0),
    ("m", "km"): (1e-3, 0.0),
    ("K", "°C"): (1.0, -273.15),
    ("Pa", "bar"): (1e-5, 0.0),
    ("1", "%"): (100.0, 0.0),
}

# Default display unit for each stored unit (applies to every model).
# Deliberately not m → km (short distances) or "1" → % (not every ratio is a percentage).
DEFAULT_DISPLAY = {
    "m/s": "km/h",
    "rad/s": "rpm",
    "J": "kWh",
    "W": "kW",
    "K": "°C",
    "Pa": "bar",
}


def display_unit(unit: str, preferred: str | None = None) -> str | None:
    """The unit to show values in, or None if the stored unit is already readable."""
    target = preferred or DEFAULT_DISPLAY.get(unit)
    if target and target != unit and (unit, target) in CONVERSIONS:
        return target
    return None


def convert(value: float, unit: str, target: str) -> float:
    factor, offset = CONVERSIONS[(unit, target)]
    return value * factor + offset
