"""The meters' settings — holding registers (FC03), written with FC16 (§3.2).

Settings change only when someone writes them, so they are their own component:
a poll does not read them, and a consumer that wants them refreshes this on
whatever schedule suits it.

The counter resets sit in the same block but are a component of their own:
"if 1 is written, set counter to 0" says what a write does and nothing about
what a read returns, so they are written and never polled.

One layout covers all six models, narrowed per model with ``restrict_fields``
— the settings a model lacks are scattered through the block rather than
grouped, and a settings read happens once per setup, where the extra round
trips a narrowing costs do not matter. An excluded setting reads as ``None``
and cannot be written.
"""

from __future__ import annotations

from typing import Any

from modbus_connection.model import Component, NumberField, enum

from .enums import (
    BaudRate,
    CtRatio,
    DataFormat,
    PulseConstant,
    SerialFormat,
    TariffSelection,
)
from .model import unscaled

ADDRESS_MIN = 1
ADDRESS_MAX = 247
PULSE_WIDTH_MIN = 2
PULSE_WIDTH_MAX = 99


def _valid_address(value: Any) -> int:
    """Reject an address the spec's 1-247 range does not allow."""
    address = int(value)
    if not ADDRESS_MIN <= address <= ADDRESS_MAX:
        raise ValueError(f"communication address must be {ADDRESS_MIN}-{ADDRESS_MAX}")
    return address


def _valid_pulse_width(value: Any) -> int:
    """Reject an S0 pulse width outside the spec's 2-99 ms."""
    width = int(value)
    if not PULSE_WIDTH_MIN <= width <= PULSE_WIDTH_MAX:
        raise ValueError(f"pulse width must be {PULSE_WIDTH_MIN}-{PULSE_WIDTH_MAX} ms")
    return width


def _reset_command(value: Any) -> int:
    """Only 1 resets a counter; the spec gives no other value a meaning."""
    if int(value) != 1:
        raise ValueError("a counter reset is written as 1")
    return 1


class Parameters(Component):
    """The meter's communication, pulse-output and tariff settings."""

    communication_format: NumberField[SerialFormat] = enum(
        0x0012, SerialFormat, count=2, writable=True
    )
    """Parity and stop bits, default one stop bit and no parity."""

    communication_address = unscaled(0x0014, writable=_valid_address)
    """The Modbus unit id, 1-247.

    A successful write takes effect immediately, so the ``ModbusUnit`` this
    component was built from no longer addresses the meter: build a new unit
    at the new id.
    """

    baud_rate: NumberField[BaudRate] = enum(0x001C, BaudRate, count=2, writable=True)
    """The link speed, default 9600. An unassigned code decodes to ``None``."""

    data_format: NumberField[DataFormat] = enum(
        0x001E, DataFormat, count=2, writable=True
    )
    """Whether the meter encodes its measurements as integers or floats.

    Only ``INTEGER``, the default, is modelled — see
    :class:`~eltako_modbus.series16.enums.DataFormat`. Writing ``FLOAT`` makes
    every measurement of this library decode to nonsense.
    """

    s0_import_pulse_width = unscaled(0x0056, writable=_valid_pulse_width)
    """Width of an import pulse on the S0 output, 2-99 ms."""

    s0_export_pulse_width = unscaled(0x0058, writable=_valid_pulse_width)
    """Width of an export pulse on the S0 output, 2-99 ms."""

    tariff_selection: NumberField[TariffSelection] = enum(
        0x005A, TariffSelection, count=2, writable=True
    )
    """Which tariff counts, or that the E2/E3/E4 wiring decides."""

    s0_import_pulse_constant: NumberField[PulseConstant] = enum(
        0xF910, PulseConstant, count=2, writable=True
    )
    """Import pulses per kWh on the S0 output."""

    s0_export_pulse_constant: NumberField[PulseConstant] = enum(
        0xF912, PulseConstant, count=2, writable=True
    )
    """Export pulses per kWh on the S0 output."""

    ct_ratio: NumberField[CtRatio] = enum(0xF914, CtRatio, count=2, writable=True)
    """The current-transformer ratio, on the meters that are wired through one."""

    reverse_measurement_direction: NumberField[bool] = NumberField(
        0xF916, count=2, signed=False, convert={0: False, 1: True}, writable=True
    )
    """Whether the meter counts current the other way round, default off."""


class Resets(Component):
    """The counter resets: write 1 to zero the counter a field names.

    Never polled — the spec documents what writing 1 does and nothing about
    what these registers read back — so nothing here is a value to look at.
    """

    total_import_active_energy = unscaled(0x005C, writable=_reset_command)
    total_export_active_energy = unscaled(0x005E, writable=_reset_command)
    tariff_1_import_active_energy = unscaled(0x0060, writable=_reset_command)
    tariff_1_export_active_energy = unscaled(0x0062, writable=_reset_command)
    tariff_2_import_active_energy = unscaled(0x0064, writable=_reset_command)
    tariff_2_export_active_energy = unscaled(0x0066, writable=_reset_command)
    tariff_3_import_active_energy = unscaled(0x0068, writable=_reset_command)
    tariff_3_export_active_energy = unscaled(0x006A, writable=_reset_command)
    tariff_4_import_active_energy = unscaled(0x006C, writable=_reset_command)
    tariff_4_export_active_energy = unscaled(0x006E, writable=_reset_command)


# The Support column of §3.2, as the feature groups the six models combine.
COMMON_PARAMETERS = (
    "communication_format",
    "communication_address",
    "baud_rate",
    "data_format",
    "s0_import_pulse_width",
    "tariff_selection",
    "s0_import_pulse_constant",
)
EXPORT_PARAMETERS = ("s0_export_pulse_width", "s0_export_pulse_constant")
TRANSFORMER_PARAMETERS = ("ct_ratio",)
THREE_PHASE_PARAMETERS = ("reverse_measurement_direction",)

COMMON_RESETS = (
    "total_import_active_energy",
    "tariff_1_import_active_energy",
    "tariff_2_import_active_energy",
)
EXPORT_RESETS = (
    "total_export_active_energy",
    "tariff_1_export_active_energy",
    "tariff_2_export_active_energy",
)
THREE_PHASE_RESETS = (
    "tariff_3_import_active_energy",
    "tariff_4_import_active_energy",
)
THREE_PHASE_EXPORT_RESETS = (
    "tariff_3_export_active_energy",
    "tariff_4_export_active_energy",
)
