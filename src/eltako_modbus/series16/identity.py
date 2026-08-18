"""The identity block at 0xFC00 — holding registers, read once (spec §3.2).

Its own component rather than part of :mod:`~eltako_modbus.series16.parameters`
because it sits some 63000 registers past the settings: no read could ever
cover both.
"""

from __future__ import annotations

from modbus_connection.model import Component, NumberField, enum, string

from ..bcd import bcd_digits
from .enums import MeterMode
from .model import unscaled

METER_MODE = 0xFC0C


class Identity(Component):
    """What the meter is — fixed for its life."""

    # 0xFC04-0xFC07 are undocumented, so the two documented runs are declared
    # apart and never read over.
    register_ranges = ((0xFC00, 0xFC03), (0xFC08, 0xFC0F))

    serial_number: NumberField[str] = NumberField(
        0xFC00, count=2, signed=False, convert=bcd_digits
    )
    """Eight BCD digits. A value that is not BCD decodes to ``None``."""

    manufacturing_code = unscaled(0xFC02)
    """The spec gives its format as ``0000000D`` without saying what ``D``
    denotes, so it is left as the raw unsigned value."""

    _sales_manufacturer = string(0xFC08, 4)

    meter_mode: NumberField[MeterMode] = enum(METER_MODE, MeterMode, count=2)
    """Which of the seven models this is. An unassigned code decodes to ``None``."""

    software_version = unscaled(0xFC0E)
    """Format ``00NNNNNN``, data type int — so the raw unsigned value. The spec
    does not say how the digits split into a version, nor whether they are BCD
    as the serial number's are."""

    @property
    def sales_manufacturer(self) -> str | None:
        """The eight ASCII characters of 0xFC08-0xFC0B, space padding removed."""
        raw = self._sales_manufacturer
        return raw.rstrip() if raw is not None else None
