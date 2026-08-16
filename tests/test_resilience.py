"""How a poll behaves when the meter or the link misbehaves."""

from __future__ import annotations

import pytest
from modbus_connection import (
    IllegalDataAddressError,
    IllegalFunctionError,
    ModbusConnectionError,
    ModbusTimeoutError,
)
from modbus_connection.mock import MockModbusUnit

from eltako_modbus import Dsz15dzmod

from .conftest import SERIAL


async def test_a_silent_meter_raises_rather_than_reporting(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """Nothing answered, so the poll does not pretend it half worked.

    With measurements the only polled component, the "first block timed out"
    rule always applies: a timeout is never contained. That is the point of the
    rule on a 9600-baud bus — waiting out a second timeout buys nothing.
    """
    mock_modbus_unit.fail_requests(ModbusTimeoutError())
    with pytest.raises(ModbusTimeoutError):
        await meter.async_update()


async def test_a_dead_link_raises(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    mock_modbus_unit.fail_requests(ModbusConnectionError())
    with pytest.raises(ModbusConnectionError):
        await meter.async_update()


async def test_a_refused_block_is_reported_not_raised(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """A Modbus exception is the meter answering, so the poll returns a report."""
    await meter.async_update()
    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")

    report = await meter.async_update()

    assert not report.complete
    assert report.updated == set()
    assert isinstance(report.failed["measurements"], IllegalDataAddressError)


async def test_values_survive_a_failed_poll(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    await meter.async_update()
    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")

    await meter.async_update()

    assert meter.measurements.voltage_l1 == pytest.approx(230.12)


async def test_listeners_fire_only_for_what_refreshed(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    fired: list[str] = []
    meter.measurements.add_update_listener(lambda: fired.append("measurements"))

    await meter.async_update()
    assert fired == ["measurements"]

    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")
    await meter.async_update()
    assert fired == ["measurements"]  # the failed poll notified nobody


@pytest.mark.parametrize("error", [IllegalDataAddressError, IllegalFunctionError])
async def test_a_meter_without_an_identity_block_still_polls(
    meter: Dsz15dzmod,
    mock_modbus_unit: MockModbusUnit,
    error: type[Exception],
) -> None:
    """The readings do not depend on 0xFC00, so a refusal there is not fatal."""
    mock_modbus_unit.fail_read(0xFC00, error())

    report = await meter.async_update()

    assert report.complete
    assert meter.identity.serial_number is None
    assert meter.measurements.voltage_l1 == pytest.approx(230.12)


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


async def test_read_raw_survives_a_missing_identity_block(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    mock_modbus_unit.fail_read(0xFC00, IllegalDataAddressError())

    raw = await meter.async_read_raw()

    assert 0xFC00 not in raw["holding"]
    assert raw["input"][0x0000] == 0x0000


async def test_read_raw_raises_when_a_polled_block_is_refused(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """There the refusal is the thing a diagnostics download wants to show."""
    mock_modbus_unit.fail_read(0x0000, IllegalDataAddressError(), register_type="input")
    with pytest.raises(IllegalDataAddressError):
        await meter.async_read_raw()
