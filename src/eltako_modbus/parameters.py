"""The meter's configuration — holding registers (FC03), written with FC16.

These change only when someone writes them, so they are their own component: a
poll does not read them, and a consumer that wants them refreshes this on
whatever schedule suits it. Addresses and defaults are spec §3.2.
"""

from __future__ import annotations

from typing import Any

from modbus_connection.model import Component, NumberField, enum

from .enums import BaudRate
from .model import unscaled

ADDRESS_MIN = 1
ADDRESS_MAX = 250


def _valid_address(value: Any) -> int:
    """Reject an address the spec's 1-250 range does not allow."""
    address = int(value)
    if not ADDRESS_MIN <= address <= ADDRESS_MAX:
        raise ValueError(f"communication address must be {ADDRESS_MIN}-{ADDRESS_MAX}")
    return address


class Parameters(Component):
    """The meter's communication and pulse settings."""

    communication_check_and_stop_bit = unscaled(0x0012)
    """Framing and checking. The spec documents only 0: one stop bit, no checking."""

    communication_address = unscaled(0x0014, writable=_valid_address)
    """The Modbus unit id, 1-250.

    A successful write takes effect immediately, so the ``ModbusUnit`` this
    component was built from no longer addresses the meter: build a new unit at
    the new id.
    """

    baud_rate: NumberField[BaudRate] = enum(0x001C, BaudRate, count=2)
    """The link speed, default 9600. An unassigned code decodes to ``None``."""

    pulse_mode = unscaled(0x0056)
    """What the S0 pulse output counts, default 2.

    Left an integer because the spec's own table cannot be enumerated: it reads
    "1 reverse active, 2 Total active, 2-4 positive active", giving code 2 two
    different meanings. See the README.
    """
