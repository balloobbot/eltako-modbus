"""The DSZ15DZMOD's decoding, identity and parameters, over the mock backend."""

from __future__ import annotations

import pytest
from modbus_connection import IllegalDataValueError
from modbus_connection.mock import MockModbusUnit, WriteEvent

from eltako_modbus import BaudRate, Dsz15dzmod

from .conftest import SERIAL, words


async def test_measurements(meter: Dsz15dzmod) -> None:
    await meter.async_update()
    m = meter.measurements
    assert m.voltage_l1 == pytest.approx(230.12)
    assert m.voltage_l2 == pytest.approx(229.87)
    assert m.voltage_l3 == pytest.approx(231.50)
    assert m.current_l1 == pytest.approx(4.31)
    assert m.current_l2 == pytest.approx(12.50)
    assert m.current_l3 == pytest.approx(0.0)


async def test_power_is_an_unscaled_signed_integer(meter: Dsz15dzmod) -> None:
    """The spec gives power no decimals, so the raw value is handed back as-is."""
    await meter.async_update()
    m = meter.measurements
    assert m.active_power_l1 == 1
    assert m.active_power_l2 == 3
    assert m.active_power_l3 == -2
    assert m.total_active_power == 2


async def test_power_factor_is_signed_with_three_decimals(meter: Dsz15dzmod) -> None:
    await meter.async_update()
    m = meter.measurements
    assert m.power_factor_l1 == pytest.approx(0.970)
    assert m.power_factor_l2 == pytest.approx(-0.864)
    assert m.power_factor_l3 == pytest.approx(1.0)
    assert m.total_power_factor == pytest.approx(0.955)


async def test_decodes_the_specs_own_energy_frame(meter: Dsz15dzmod) -> None:
    """Spec §2.1.2 answers 'CC 04 08 00 00 01 CD 00 00 01 70 CF D7' for 0x0048.

    That frame is the one place the document states a wire value and its
    meaning together, and it is what pins two decimals and high-word-first.
    """
    await meter.async_update()
    m = meter.measurements
    assert m.total_import_active_energy == pytest.approx(4.61)
    assert m.total_export_active_energy == pytest.approx(3.68)
    assert m.part_import_active_energy == pytest.approx(123.45)
    assert m.part_export_active_energy == pytest.approx(6.00)


async def test_identity_is_read_by_setup(meter: Dsz15dzmod) -> None:
    await meter.async_update()
    assert meter.identity.serial_number == SERIAL
    assert meter.identity.meter_code == 13


async def test_a_serial_that_is_not_bcd_decodes_to_none(
    mock_modbus_unit: MockModbusUnit,
) -> None:
    mock_modbus_unit.holding[0xFC00] = [0x2048, 0x13AF]  # A and F are not BCD digits
    meter = Dsz15dzmod(mock_modbus_unit)
    await meter.async_update()
    assert meter.identity.serial_number is None


async def test_the_parameters_are_read_at_setup(meter: Dsz15dzmod) -> None:
    """They are read-only but for the address, so one read covers the meter's life."""
    await meter.async_update()

    assert meter.parameters.baud_rate is BaudRate.BPS_9600
    assert meter.parameters.communication_address == 204
    assert meter.parameters.communication_check_and_stop_bit == 0
    assert meter.parameters.pulse_mode == 2


async def test_an_unassigned_baud_code_decodes_to_none(
    mock_modbus_unit: MockModbusUnit,
) -> None:
    mock_modbus_unit.holding[0x001C] = words(4)  # the spec assigns no code 4
    meter = Dsz15dzmod(mock_modbus_unit)
    await meter.parameters.async_update()
    assert meter.parameters.baud_rate is None


async def test_writing_the_communication_address(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    """A 32-bit parameter goes out as one FC16 write of two registers."""
    writes: list[WriteEvent] = []
    mock_modbus_unit.on_write(writes.append)

    await meter.parameters.write("communication_address", 42)

    assert len(writes) == 1
    assert writes[0].function_code == 0x10
    assert writes[0].address == 0x0014
    assert writes[0].values == [0x0000, 0x002A]


@pytest.mark.parametrize("value", [0, 251, -1])
async def test_an_out_of_range_communication_address_is_refused(
    meter: Dsz15dzmod, value: int
) -> None:
    """The spec's 1-250 range is enforced before anything reaches the bus."""
    with pytest.raises(ValueError, match="1-250"):
        await meter.parameters.write("communication_address", value)


async def test_the_measurements_are_read_only(meter: Dsz15dzmod) -> None:
    with pytest.raises(AttributeError):
        await meter.measurements.write("voltage_l1", 230.0)


async def test_a_rejected_write_leaves_the_value_alone(
    meter: Dsz15dzmod, mock_modbus_unit: MockModbusUnit
) -> None:
    mock_modbus_unit.fail_write(0x0014, IllegalDataValueError())
    with pytest.raises(IllegalDataValueError):
        await meter.parameters.write("communication_address", 42)

    await meter.parameters.async_update()
    assert meter.parameters.communication_address == 204
