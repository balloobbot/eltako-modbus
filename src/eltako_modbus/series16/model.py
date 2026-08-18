"""Field presets for the 32-bit layout of the DSZ16/WSZ16 register map.

Every value in the map — measurement or setting — is 4 bytes over two
consecutive registers, high word in the lower address (spec §1.2.2 and the
worked frames of §2.1.2 and §2.2.2). That is ``count=2`` with the default
``word_order="big"``, so the helpers below spell out only the scaling rules
the spec's Remarks state.
"""

from __future__ import annotations

from modbus_connection.model import NumberField, WriteValidator, int32, uint32

ENERGY_SCALE = 0.01
"""Two decimals — the Remarks' general rule."""

CT_ENERGY_SCALE = 0.1
"""One decimal, on the transformer-connected DSZ16WD and DSZ16WDZ (Note 1)."""


def scaled(address: int, *, unit: str) -> NumberField[float]:
    """An unsigned measurement with two decimals — the Remarks' general rule."""
    return uint32(address, scale=0.01, unit=unit)


def energy(address: int, scale: float, *, unit: str = "kWh") -> NumberField[float]:
    """An energy counter, at the two decimals of its meter (see Note 1)."""
    return uint32(address, scale=scale, unit=unit)


def power(address: int, *, unit: str) -> NumberField[int]:
    """A signed power measurement in whole W, VA or var, as the Remarks state.

    "Power is a signed number without decimal", so the raw value is the value.
    Note that this contradicts the DSZ15DZMOD's own datasheet, which gives the
    same register a unit of kW; V3.7.4 says W for that model too. It also
    settles nothing about apparent and reactive power: the Remarks name only
    "power", and this models VA and var by the same rule, which is what the
    unit column and the missing decimals together imply — but the spec never
    says so, and only hardware could.
    """
    return int32(address, unit=unit)


def power_factor(address: int) -> NumberField[float]:
    """A signed power factor or cosφ with three decimals."""
    return int32(address, scale=0.001)


def unscaled(
    address: int, *, writable: bool | WriteValidator = False
) -> NumberField[int]:
    """An unsigned setting word, read as-is.

    The Remarks' scaling rules head the coding sheet's input registers; the
    holding-register table states no scale, and every documented value there
    is a small count or code.
    """
    return uint32(address, writable=writable)
