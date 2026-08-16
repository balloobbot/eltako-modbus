"""What a poll actually costs on the wire.

The meter sits on a 9600-baud RS-485 link, so the number of requests is the
number that matters, and it is pinned here rather than left to drift.
"""

from __future__ import annotations

from modbus_connection.mock import MockModbusUnit

from eltako_modbus import Dsz15dzmod


async def test_a_poll_costs_three_reads(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """Eighteen measurements, three round-trips.

    The planner merges fields within ``max_gap`` (16) of each other, so the
    documented holes of 12, 8 and 8 registers are read over and only the two
    wider ones — 16 registers before 0x0034 and 20 before 0x0060 — split the
    block. Reading the values one at a time would cost eighteen requests, and
    the whole span in one would cost a single 100-register read the spec does
    not license, since it never says the meter answers for the holes.
    """
    await meter.async_update()  # first poll: setup reads the identity block
    mock_modbus_unit.read_events.clear()

    await meter.async_update()

    blocks = mock_modbus_unit.read_events
    assert [(b.register_type, b.address, b.count) for b in blocks] == [
        ("input", 0x0000, 36),  # voltages, currents, powers, power factors
        ("input", 0x0034, 24),  # total power, total power factor, total energy
        ("input", 0x0060, 4),  # part energy
    ]
    assert len(blocks) == 3


async def test_setup_adds_one_read_to_the_first_poll_only(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """The identity block is four contiguous registers, read once."""
    await meter.async_update()

    identity = [b for b in mock_modbus_unit.read_events if b.register_type == "holding"]
    assert [(b.address, b.count) for b in identity] == [(0xFC00, 4)]

    mock_modbus_unit.read_events.clear()
    await meter.async_update()
    assert all(b.register_type == "input" for b in mock_modbus_unit.read_events)


async def test_the_parameters_cost_two_reads_when_asked_for(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """0x0056 is 56 registers past the rest, so it cannot share their block."""
    await meter.parameters.async_update()

    assert [
        (b.register_type, b.address, b.count) for b in mock_modbus_unit.read_events
    ] == [
        ("holding", 0x0012, 12),  # stop bit, address, baud rate
        ("holding", 0x0056, 2),  # pulse mode
    ]


async def test_read_raw_covers_every_register_the_meter_serves(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """A diagnostics dump adds the identity and the settings a poll skips."""
    raw = await meter.async_read_raw()

    assert set(raw) == {"holding", "input"}
    assert len(raw["input"]) == 64  # 36 + 24 + 4
    assert list(raw["holding"]) == [
        *range(0x0012, 0x001E),
        0x0056,
        0x0057,
        *range(0xFC00, 0xFC04),
    ]
    assert len(mock_modbus_unit.read_events) == 6  # 3 input, 3 holding
