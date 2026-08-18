"""What a poll of a DSZ16 or WSZ16 costs on the wire.

These meters sit on a 9600-baud RS-485 link, so the number of requests is the
number that matters, and it is pinned here rather than left to drift.
"""

from __future__ import annotations

from modbus_connection.mock import MockModbusUnit

from eltako_modbus import Dsz16dz, Wsz16d


async def test_a_three_phase_poll_costs_two_reads(
    dsz16dz: Dsz16dz, mock_modbus_unit: MockModbusUnit
) -> None:
    """Sixty measurements, two round-trips.

    The map's holes are all narrower than ``max_gap`` (16), so the planner
    reads over them and only the 125-register ceiling on a single request
    splits the block — before tariff 4, which the twelve-register hole ahead
    of it happens to sit next to.
    """
    await dsz16dz.async_update()  # first poll: setup reads the fixed blocks
    mock_modbus_unit.read_events.clear()

    await dsz16dz.async_update()

    blocks = mock_modbus_unit.read_events
    assert [(b.register_type, b.address, b.count) for b in blocks] == [
        ("input", 0x0000, 124),  # everything up to tariff 3
        ("input", 0x0084, 22),  # tariff 4, the per-phase energy, the tariff in force
    ]


async def test_a_single_phase_poll_costs_three_reads(
    wsz16d: Wsz16d, mock_modbus_unit: MockModbusUnit
) -> None:
    """A WSZ16 declares fewer points, so its blocks stop where they run out."""
    await wsz16d.async_update()
    mock_modbus_unit.read_events.clear()

    await wsz16d.async_update()

    blocks = mock_modbus_unit.read_events
    assert [(b.register_type, b.address, b.count) for b in blocks] == [
        ("input", 0x0000, 32),  # voltage, current, power, power factor
        ("input", 0x0034, 60),  # totals, frequency, energy
        ("input", 0x0098, 2),  # the tariff in force
    ]


async def test_setup_reads_the_fixed_blocks_once(
    dsz16dz: Dsz16dz, mock_modbus_unit: MockModbusUnit
) -> None:
    """The identity's two documented runs, then the settings."""
    await dsz16dz.async_update()

    fixed = [b for b in mock_modbus_unit.read_events if b.register_type == "holding"]
    assert [(b.address, b.count) for b in fixed] == [
        (0xFC00, 4),  # serial number and manufacturing code
        (0xFC08, 8),  # sales manufacturer, meter mode, software version
        (0x0012, 14),  # format, address, baud rate, data format
        (0x0056, 6),  # pulse widths and tariff selection
        (0xF910, 4),  # the pulse constants
        (0xF916, 2),  # reverse measurement direction
    ]

    mock_modbus_unit.read_events.clear()
    await dsz16dz.async_update()
    assert all(b.register_type == "input" for b in mock_modbus_unit.read_events)


async def test_a_model_without_a_setting_never_reads_it(
    wsz16d: Wsz16d, mock_modbus_unit: MockModbusUnit
) -> None:
    """0xF914 lies between two settings a WSZ16D does have, and stays unread."""
    await wsz16d.parameters.async_update()

    read = [(b.address, b.count) for b in mock_modbus_unit.read_events]
    assert read == [
        (0x0012, 14),
        (0x0056, 2),  # the import pulse width, without the export one after it
        (0x005A, 2),  # the tariff selection
        (0xF910, 2),  # the import pulse constant, without the CT ratio
    ]


async def test_read_raw_covers_every_register_the_meter_is_read_from(
    dsz16dz: Dsz16dz, mock_modbus_unit: MockModbusUnit
) -> None:
    """A diagnostics dump adds the identity and the settings a poll skips."""
    raw = await dsz16dz.async_read_raw()

    assert set(raw) == {"holding", "input"}
    assert len(raw["input"]) == 146  # 124 + 22
    assert list(raw["holding"]) == [
        *range(0x0012, 0x0020),
        *range(0x0056, 0x005C),
        *range(0xF910, 0xF914),
        0xF916,
        0xF917,
        *range(0xFC00, 0xFC04),
        *range(0xFC08, 0xFC10),
    ]
    # The counter resets are written, never read, so no dump reaches them.
    assert 0x005C not in raw["holding"]
