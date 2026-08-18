"""Fixtures: an Eltako meter over modbus-connection's in-memory mock backend.

Every value is 32 bits over two registers, high word first, so each seeded
entry below is a two-word list. There are no coils and no discrete inputs.
"""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit

from eltako_modbus import (
    Dsz15dzmod,
    Dsz16d,
    Dsz16dz,
    Dsz16wd,
    Dsz16wdz,
    MeterMode,
    Wsz16d,
    Wsz16dz,
)


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


# The DSZ16/WSZ16 map of spec V3.7.4. One seed serves every model: each reads
# the subset of it that its own layout declares.
SERIES16_INPUT: dict[int, int | list[int]] = {
    0x0000: words(23012),  # voltage L1 -> 230.12 V
    0x0002: words(22987),  # voltage L2 -> 229.87 V
    0x0004: words(23150),  # voltage L3 -> 231.50 V
    0x0006: words(431),  # current L1 -> 4.31 A
    0x0008: words(1250),  # current L2 -> 12.50 A
    0x000A: words(0),  # current L3 -> 0.00 A
    0x000C: words(990),  # L1 active power -> 990 W
    0x000E: words(2875),  # L2 active power -> 2875 W
    0x0010: words(twos_complement(-450)),  # L3 active power -> -450 W, exporting
    0x0012: words(1020),  # L1 apparent power -> 1020 VA
    0x0014: words(2900),
    0x0016: words(500),
    0x0018: words(240),  # L1 reactive power -> 240 var
    0x001A: words(twos_complement(-300)),
    0x001C: words(0),
    0x001E: words(970),  # L1 power factor -> 0.970
    0x0020: words(twos_complement(-864)),
    0x0022: words(1000),
    0x0024: words(980),  # L1 cosφ -> 0.980
    0x0026: words(twos_complement(-870)),
    0x0028: words(999),
    0x0034: words(3415),  # total active power -> 3415 W
    0x0036: words(4420),  # total apparent power -> 4420 VA
    0x0038: words(twos_complement(-60)),  # total reactive power -> -60 var
    0x003E: words(955),  # total power factor -> 0.955
    0x0040: words(962),  # total cosφ -> 0.962
    0x0046: words(5001),  # frequency -> 50.01 Hz
    # The spec's own worked frame (§2.2.2): 4.61 kWh in and 3.68 kWh out.
    0x0048: [0x0000, 0x01CD, 0x0000, 0x0170],
    0x0050: words(88),  # neutral current -> 0.88 A
    0x0052: words(1234),  # total positive reactive energy -> 12.34 kvarh
    0x0054: words(567),  # total negative reactive energy -> 5.67 kvarh
    0x0056: words(39812),  # voltage L1-L2 -> 398.12 V
    0x0058: words(39750),
    0x005A: words(39900),
    0x0060: words(12345),  # resettable total import -> 123.45 kWh
    0x0062: words(600),  # resettable total export -> 6.00 kWh
    0x0064: words(10000),  # tariff 1 import -> 100.00 kWh
    0x0066: words(2500),
    0x0068: words(300),  # tariff 1 export -> 3.00 kWh
    0x006A: words(100),
    0x006C: words(5000),  # tariff 2 import -> 50.00 kWh
    0x006E: words(1500),
    0x0070: words(200),
    0x0072: words(50),
    0x0074: words(400),  # tariff 3 import -> 4.00 kWh
    0x0076: words(100),
    0x0078: words(0),
    0x007A: words(0),
    0x0084: words(900),  # tariff 4 import -> 9.00 kWh
    0x0086: words(200),
    0x0088: words(0),
    0x008A: words(0),
    0x008C: words(4000),  # import active energy L1 -> 40.00 kWh
    0x008E: words(5000),
    0x0090: words(3345),
    0x0092: words(100),  # export active energy L1 -> 1.00 kWh
    0x0094: words(200),
    0x0096: words(68),
    0x0098: words(1),  # selected tariff -> tariff 1
}

SERIES16_HOLDING: dict[int, int | list[int]] = {
    0x0012: words(0),  # one stop bit, no parity
    0x0014: words(204),  # communication address -> 204 (0xCC, the spec's example)
    0x001C: words(5),  # baud rate -> 9600
    0x001E: words(0),  # data format -> integer
    0x0056: words(30),  # S0 import pulse width -> 30 ms
    0x0058: words(30),  # S0 export pulse width -> 30 ms
    0x005A: words(0),  # tariff selection -> the E2/E3/E4 wiring decides
    0xF910: words(6),  # S0 import pulse constant -> 1000 imp/kWh
    0xF912: words(6),
    0xF914: words(2),  # CT ratio -> 50:5
    0xF916: words(0),  # reverse measurement direction -> off
    0xFC00: [0x2048, 0x1337],  # serial number, packed BCD -> "20481337"
    0xFC02: words(13),  # manufacturing code
    0xFC08: [0x454C, 0x5441, 0x4B4F, 0x2020],  # "ELTAKO  "
    0xFC0E: words(374),  # software version
}


def series16_unit(unit: MockModbusUnit, meter_mode: int) -> MockModbusUnit:
    """Seed *unit* with the V3.7.4 map, reporting the given model code."""
    unit.input.update(SERIES16_INPUT)
    unit.holding.update(SERIES16_HOLDING)
    unit.holding[0xFC0C] = words(meter_mode)
    return unit


@pytest.fixture
def dsz16d(mock_modbus_unit: MockModbusUnit) -> Dsz16d:
    """A three-phase meter that counts one direction."""
    return Dsz16d(series16_unit(mock_modbus_unit, MeterMode.DSZ16D))


@pytest.fixture
def dsz16dz(mock_modbus_unit: MockModbusUnit) -> Dsz16dz:
    """A three-phase meter that counts both directions."""
    return Dsz16dz(series16_unit(mock_modbus_unit, MeterMode.DSZ16DZ))


@pytest.fixture
def dsz16wd(mock_modbus_unit: MockModbusUnit) -> Dsz16wd:
    """A transformer-connected meter — the same map, one decimal of energy."""
    return Dsz16wd(series16_unit(mock_modbus_unit, MeterMode.DSZ16WD))


@pytest.fixture
def dsz16wdz(mock_modbus_unit: MockModbusUnit) -> Dsz16wdz:
    """A transformer-connected meter that counts both directions."""
    return Dsz16wdz(series16_unit(mock_modbus_unit, MeterMode.DSZ16WDZ))


@pytest.fixture
def wsz16d(mock_modbus_unit: MockModbusUnit) -> Wsz16d:
    """A single-phase meter that counts one direction."""
    return Wsz16d(series16_unit(mock_modbus_unit, MeterMode.WSZ16D))


@pytest.fixture
def wsz16dz(mock_modbus_unit: MockModbusUnit) -> Wsz16dz:
    """A single-phase meter that counts both directions."""
    return Wsz16dz(series16_unit(mock_modbus_unit, MeterMode.WSZ16DZ))
