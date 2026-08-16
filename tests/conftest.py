"""Fixtures: a Dsz15dzmod over modbus-connection's in-memory mock backend.

Every value is 32 bits over two registers, high word first, so each seeded
entry below is a two-word list. There are no coils and no discrete inputs.
"""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit

from eltako_modbus import Dsz15dzmod


def words(value: int) -> list[int]:
    """Split a 32-bit raw value into its two registers, high word first."""
    return [(value >> 16) & 0xFFFF, value & 0xFFFF]


def twos_complement(value: int) -> int:
    """The 32-bit raw pattern a negative value is stored as."""
    return value & 0xFFFFFFFF


SERIAL = "20481337"

# Raw input words keyed by address; the decoded view is inline.
INPUT: dict[int, int | list[int]] = {
    0x0000: words(23012),  # voltage L1 -> 230.12 V
    0x0002: words(22987),  # voltage L2 -> 229.87 V
    0x0004: words(23150),  # voltage L3 -> 231.50 V
    0x0006: words(431),  # current L1 -> 4.31 A
    0x0008: words(1250),  # current L2 -> 12.50 A
    0x000A: words(0),  # current L3 -> 0.00 A
    0x000C: words(1),  # L1 active power -> 1 (kW per the spec; see README)
    0x000E: words(3),  # L2 active power -> 3
    0x0010: words(twos_complement(-2)),  # L3 active power -> -2, exporting
    0x001E: words(970),  # L1 power factor -> 0.970
    0x0020: words(twos_complement(-864)),  # L2 power factor -> -0.864
    0x0022: words(1000),  # L3 power factor -> 1.000
    0x0034: words(2),  # total active power -> 2
    0x003E: words(955),  # total power factor -> 0.955
    # The spec's own worked frame (§2.1.2): 4.61 kWh in and 3.68 kWh out.
    0x0048: [0x0000, 0x01CD, 0x0000, 0x0170],
    0x0060: words(12345),  # part import active energy -> 123.45 kWh
    0x0062: words(600),  # part export active energy -> 6.00 kWh
}

# Raw holding words keyed by address.
HOLDING: dict[int, int | list[int]] = {
    0x0012: words(0),  # one stop bit, no checking
    0x0014: words(204),  # communication address -> 204 (0xCC, the spec's example)
    0x001C: words(2),  # baud rate -> 9600
    0x0056: words(2),  # pulse mode -> 2
    0xFC00: [0x2048, 0x1337],  # serial number, packed BCD -> "20481337"
    0xFC02: words(13),  # meter code
}


@pytest.fixture
def meter(mock_modbus_unit: MockModbusUnit) -> Dsz15dzmod:
    """A Dsz15dzmod over the mock unit, preloaded with device values."""
    mock_modbus_unit.input.update(INPUT)
    mock_modbus_unit.holding.update(HOLDING)
    return Dsz15dzmod(mock_modbus_unit)
