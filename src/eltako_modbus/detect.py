"""Ask a meter which model it is, and build the device object for it.

Register 0xFC0C carries a code per model (spec §3.2), and every meter the spec
covers answers it — including the DSZ15DZMOD, whose own datasheet does not
document the register.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from modbus_connection.model import Component

from .dsz15dzmod import Dsz15dzmod
from .series16 import (
    Dsz16d,
    Dsz16dz,
    Dsz16wd,
    Dsz16wdz,
    MeterMode,
    Series16Meter,
    Wsz16d,
    Wsz16dz,
)
from .series16.identity import METER_MODE
from .series16.model import unscaled

if TYPE_CHECKING:
    from collections.abc import Callable

    from modbus_connection import ModbusUnit

EltakoMeter = Dsz15dzmod | Series16Meter[Any]

MODELS: dict[MeterMode, Callable[[ModbusUnit], EltakoMeter]] = {
    MeterMode.DSZ15DZMOD: Dsz15dzmod,
    MeterMode.DSZ16D: Dsz16d,
    MeterMode.DSZ16DZ: Dsz16dz,
    MeterMode.DSZ16WD: Dsz16wd,
    MeterMode.DSZ16WDZ: Dsz16wdz,
    MeterMode.WSZ16D: Wsz16d,
    MeterMode.WSZ16DZ: Wsz16dz,
}


class _ModelProbe(Component):
    """Just the model code, so detection costs one two-register read."""

    meter_mode = unscaled(METER_MODE)


async def async_detect_meter(unit: ModbusUnit) -> EltakoMeter:
    """Build the device object for the meter behind *unit*.

    Raises ``ValueError`` if it reports a code no model of the spec has, and
    whatever the read raised if it did not answer at all.
    """
    probe = _ModelProbe(unit)
    await probe.async_update()
    code = probe.meter_mode
    model = next((cls for mode, cls in MODELS.items() if mode == code), None)
    if model is None:
        raise ValueError(f"the meter reports meter mode {code}, which names no model")
    return model(unit)
