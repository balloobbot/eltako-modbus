"""The meter's identity block at 0xFC00 — holding registers, read once.

Its own component rather than part of :mod:`~eltako_modbus.parameters` because
it sits 64512 registers away: no read could ever cover both, and setup wants
this block without dragging the settings along.
"""

from __future__ import annotations

from modbus_connection.model import Component, NumberField

from .model import unscaled


def _bcd_digits(raw: int) -> str:
    """Decode a packed-BCD word into its digits; a nibble above 9 is not BCD."""
    digits = f"{raw:08x}"
    if not digits.isdigit():
        raise ValueError(f"not packed BCD: 0x{raw:08X}")
    return digits


class Identity(Component):
    """The serial number and meter code — fixed for the life of the meter."""

    serial_number: NumberField[str] = NumberField(
        0xFC00, count=2, signed=False, convert=_bcd_digits
    )
    """Eight BCD digits (spec §3.2). A value that is not BCD decodes to ``None``."""

    meter_code = unscaled(0xFC02)
    """The model code. The spec gives its format as ``0000000D`` without saying
    what ``D`` denotes, so it is left as the raw unsigned value."""
