"""How a poll behaves when the meter or the link misbehaves."""

from __future__ import annotations

import pytest
from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusTimeoutError,
)
from modbus_connection.mock import MockModbusUnit

from eltako_modbus import Dsz15dzmod

from .conftest import SERIAL


async def test_a_silent_meter_raises(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    mock_modbus_unit.fail_requests(ModbusTimeoutError())
    with pytest.raises(ModbusTimeoutError):
        await meter.async_update()


async def test_a_dead_link_raises(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    mock_modbus_unit.fail_requests(ModbusConnectionError())
    with pytest.raises(ModbusConnectionError):
        await meter.async_update()


async def test_a_refused_block_raises(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """One component is polled, so its failure is the poll's failure."""
    await meter.async_update()
    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")

    with pytest.raises(IllegalDataAddressError):
        await meter.async_update()


async def test_values_survive_a_failed_poll(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    await meter.async_update()
    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")

    with pytest.raises(IllegalDataAddressError):
        await meter.async_update()

    assert meter.measurements.voltage_l1 == pytest.approx(230.12)


async def test_a_failed_poll_notifies_nobody(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    fired: list[str] = []
    meter.measurements.add_update_listener(lambda: fired.append("measurements"))

    await meter.async_update()
    assert fired == ["measurements"]

    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")
    with pytest.raises(IllegalDataAddressError):
        await meter.async_update()
    assert fired == ["measurements"]


async def test_setup_is_retried_after_an_unreachable_meter(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """A failed setup latches nothing, so the identity is not lost forever."""
    mock_modbus_unit.fail_requests(ModbusTimeoutError())
    with pytest.raises(ModbusTimeoutError):
        await meter.async_update()
    assert meter.identity.serial_number is None

    mock_modbus_unit.fail_requests(None)
    await meter.async_update()
    assert meter.identity.serial_number == SERIAL


async def test_the_fixed_blocks_are_read_once(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """The identity and the settings cannot change, so a poll never re-reads them."""
    await meter.async_update()
    mock_modbus_unit.read_events.clear()

    await meter.async_update()

    assert all(event.register_type == "input" for event in mock_modbus_unit.read_events)


async def test_read_raw_raises_when_a_block_is_refused(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """The refusal is the thing a diagnostics download wants to show."""
    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")
    with pytest.raises(IllegalDataAddressError):
        await meter.async_read_raw()
