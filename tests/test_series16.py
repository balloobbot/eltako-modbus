"""Decoding, per-model layouts, settings and writes of the DSZ16/WSZ16 meters."""

from __future__ import annotations

import pytest
from modbus_connection.mock import MockModbusUnit, WriteEvent

from eltako_modbus import (
    Dsz15dzmod,
    Dsz16d,
    Dsz16dz,
    Dsz16wd,
    Dsz16wdz,
    MeterMode,
    Wsz16d,
    Wsz16dz,
    async_detect_meter,
)
from eltako_modbus.series16 import (
    BaudRate,
    CtRatio,
    DataFormat,
    PulseConstant,
    SerialFormat,
    Tariff,
    TariffSelection,
)

from .conftest import SERIAL, series16_unit, words


async def test_measurements(dsz16dz: Dsz16dz) -> None:
    await dsz16dz.async_update()
    m = dsz16dz.measurements
    assert m.voltage_l1 == pytest.approx(230.12)
    assert m.voltage_l3 == pytest.approx(231.50)
    assert m.current_l2 == pytest.approx(12.50)
    assert m.neutral_current == pytest.approx(0.88)
    assert m.voltage_l1_l2 == pytest.approx(398.12)
    assert m.frequency == pytest.approx(50.01)


async def test_power_is_a_signed_integer_of_the_units_column(dsz16dz: Dsz16dz) -> None:
    """The Remarks give power no decimals, so the raw value is the value."""
    await dsz16dz.async_update()
    m = dsz16dz.measurements
    assert m.active_power_l1 == 990
    assert m.active_power_l3 == -450
    assert m.apparent_power_l1 == 1020
    assert m.reactive_power_l2 == -300
    assert m.total_active_power == 3415
    assert m.total_apparent_power == 4420
    assert m.total_reactive_power == -60


async def test_power_factor_and_cos_phi_are_signed_with_three_decimals(
    dsz16dz: Dsz16dz,
) -> None:
    await dsz16dz.async_update()
    m = dsz16dz.measurements
    assert m.power_factor_l1 == pytest.approx(0.970)
    assert m.power_factor_l2 == pytest.approx(-0.864)
    assert m.cos_phi_l2 == pytest.approx(-0.870)
    assert m.total_power_factor == pytest.approx(0.955)
    assert m.total_cos_phi == pytest.approx(0.962)


async def test_decodes_the_specs_own_energy_frame(dsz16dz: Dsz16dz) -> None:
    """Spec §2.2.2 answers 'CC 04 08 00 00 01 CD 00 00 01 70 CF D7' for 0x0048.

    That frame is the one place the document states a wire value and its
    meaning together, and it is what pins two decimals and high-word-first.
    """
    await dsz16dz.async_update()
    m = dsz16dz.measurements
    assert m.total_import_active_energy == pytest.approx(4.61)
    assert m.total_export_active_energy == pytest.approx(3.68)


async def test_the_energy_counters(dsz16dz: Dsz16dz) -> None:
    await dsz16dz.async_update()
    m = dsz16dz.measurements
    assert m.resettable_total_import_active_energy == pytest.approx(123.45)
    assert m.resettable_total_export_active_energy == pytest.approx(6.00)
    assert m.total_positive_reactive_energy == pytest.approx(12.34)
    assert m.total_negative_reactive_energy == pytest.approx(5.67)
    assert m.tariff_1_import_active_energy == pytest.approx(100.00)
    assert m.tariff_1_resettable_export_active_energy == pytest.approx(1.00)
    assert m.tariff_4_import_active_energy == pytest.approx(9.00)
    assert m.import_active_energy_l1 == pytest.approx(40.00)
    assert m.export_active_energy_l3 == pytest.approx(0.68)
    assert m.selected_tariff is Tariff.TARIFF_1


async def test_a_transformer_meter_keeps_one_decimal_of_energy(
    dsz16wd: Dsz16wd, dsz16d: Dsz16d
) -> None:
    """Note 1: the same raw counter is ten times the energy on a WD or WDZ."""
    await dsz16wd.async_update()
    await dsz16d.async_update()
    assert dsz16wd.measurements.total_import_active_energy == pytest.approx(46.1)
    assert dsz16d.measurements.total_import_active_energy == pytest.approx(4.61)
    assert dsz16wd.measurements.tariff_1_import_active_energy == pytest.approx(1000.0)
    assert dsz16wd.measurements.total_positive_reactive_energy == pytest.approx(123.4)


async def test_a_one_way_meter_has_no_export_counters(dsz16d: Dsz16d) -> None:
    """The export half of the map is declared only by the bidirectional models."""
    declared = dsz16d.measurements.declared_fields
    assert "total_import_active_energy" in declared
    assert not [name for name in declared if "export" in name]
    assert "total_negative_reactive_energy" not in declared


async def test_a_single_phase_meter_declares_only_its_own_points(
    wsz16d: Wsz16d, wsz16dz: Wsz16dz
) -> None:
    """A WSZ16 has one phase, no cosφ per phase, and tariffs 1 and 2 only."""
    declared = wsz16d.measurements.declared_fields
    assert "voltage_l1" in declared
    assert not [name for name in declared if name.endswith(("_l2", "_l3"))]
    assert "cos_phi_l1" not in declared
    assert "neutral_current" not in declared
    assert "tariff_3_import_active_energy" not in declared
    assert "total_export_active_energy" in wsz16dz.measurements.declared_fields


async def test_the_single_phase_measurements(wsz16dz: Wsz16dz) -> None:
    await wsz16dz.async_update()
    m = wsz16dz.measurements
    assert m.voltage_l1 == pytest.approx(230.12)
    assert m.active_power_l1 == 990
    assert m.total_apparent_power == 4420
    assert m.total_import_active_energy == pytest.approx(4.61)
    assert m.tariff_2_export_active_energy == pytest.approx(2.00)


async def test_identity_is_read_by_setup(dsz16dz: Dsz16dz) -> None:
    await dsz16dz.async_update()
    identity = dsz16dz.identity
    assert identity.serial_number == SERIAL
    assert identity.manufacturing_code == 13
    assert identity.sales_manufacturer == "ELTAKO"
    assert identity.meter_mode is MeterMode.DSZ16DZ
    assert identity.software_version == 374


async def test_the_parameters_are_read_at_setup(dsz16wdz: Dsz16wdz) -> None:
    await dsz16wdz.async_update()
    parameters = dsz16wdz.parameters
    assert parameters.communication_format is SerialFormat.ONE_STOP_NO_PARITY
    assert parameters.communication_address == 204
    assert parameters.baud_rate is BaudRate.BPS_9600
    assert parameters.data_format is DataFormat.INTEGER
    assert parameters.s0_import_pulse_width == 30
    assert parameters.tariff_selection is TariffSelection.EXTERNAL
    assert parameters.s0_import_pulse_constant is PulseConstant.IMP_1000_PER_KWH
    assert parameters.ct_ratio is CtRatio.RATIO_50_5
    assert parameters.reverse_measurement_direction is False


async def test_a_setting_the_model_does_not_have_reads_none(wsz16d: Wsz16d) -> None:
    """A single-phase meter has no transformer and counts one way."""
    await wsz16d.async_update()
    assert wsz16d.parameters.baud_rate is BaudRate.BPS_9600
    assert wsz16d.parameters.ct_ratio is None
    assert wsz16d.parameters.s0_export_pulse_width is None
    assert wsz16d.parameters.reverse_measurement_direction is None


async def test_writing_the_communication_address(
    dsz16dz: Dsz16dz, mock_modbus_unit: MockModbusUnit
) -> None:
    """A 32-bit parameter goes out as one FC16 write of two registers."""
    writes: list[WriteEvent] = []
    mock_modbus_unit.on_write(writes.append)

    await dsz16dz.parameters.write("communication_address", 42)

    assert len(writes) == 1
    assert writes[0].function_code == 0x10
    assert writes[0].address == 0x0014
    assert writes[0].values == [0x0000, 0x002A]


@pytest.mark.parametrize("value", [0, 248, -1])
async def test_an_out_of_range_communication_address_is_refused(
    dsz16dz: Dsz16dz, value: int
) -> None:
    """The spec's 1-247 range is enforced before anything reaches the bus."""
    with pytest.raises(ValueError, match="1-247"):
        await dsz16dz.parameters.write("communication_address", value)


@pytest.mark.parametrize("value", [1, 100])
async def test_an_out_of_range_pulse_width_is_refused(
    dsz16dz: Dsz16dz, value: int
) -> None:
    with pytest.raises(ValueError, match="2-99 ms"):
        await dsz16dz.parameters.write("s0_import_pulse_width", value)


async def test_writing_a_coded_setting(
    dsz16dz: Dsz16dz, mock_modbus_unit: MockModbusUnit
) -> None:
    writes: list[WriteEvent] = []
    mock_modbus_unit.on_write(writes.append)

    await dsz16dz.parameters.write("baud_rate", BaudRate.BPS_19200)

    assert writes[0].address == 0x001C
    assert writes[0].values == words(7)


async def test_writing_a_setting_the_model_does_not_have_is_refused(
    wsz16d: Wsz16d,
) -> None:
    with pytest.raises(AttributeError):
        await wsz16d.parameters.write("ct_ratio", CtRatio.RATIO_50_5)


async def test_resetting_a_counter(
    dsz16dz: Dsz16dz, mock_modbus_unit: MockModbusUnit
) -> None:
    writes: list[WriteEvent] = []
    mock_modbus_unit.on_write(writes.append)

    await dsz16dz.resets.write("tariff_1_export_active_energy", 1)

    assert writes[0].address == 0x0062
    assert writes[0].values == words(1)


async def test_a_reset_takes_no_value_but_one(dsz16dz: Dsz16dz) -> None:
    """The spec gives a reset register no meaning other than 'write 1'."""
    with pytest.raises(ValueError, match="written as 1"):
        await dsz16dz.resets.write("total_import_active_energy", 0)


async def test_a_reset_the_model_does_not_have_is_refused(wsz16dz: Wsz16dz) -> None:
    """A WSZ16 has no tariffs 3 and 4, so it has no resets for them either."""
    await wsz16dz.resets.write("tariff_2_export_active_energy", 1)
    with pytest.raises(AttributeError):
        await wsz16dz.resets.write("tariff_3_import_active_energy", 1)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (MeterMode.DSZ15DZMOD, Dsz15dzmod),
        (MeterMode.DSZ16D, Dsz16d),
        (MeterMode.DSZ16DZ, Dsz16dz),
        (MeterMode.DSZ16WD, Dsz16wd),
        (MeterMode.DSZ16WDZ, Dsz16wdz),
        (MeterMode.WSZ16D, Wsz16d),
        (MeterMode.WSZ16DZ, Wsz16dz),
    ],
)
async def test_detection_builds_the_model_the_meter_reports(
    mock_modbus_unit: MockModbusUnit, mode: MeterMode, expected: type[object]
) -> None:
    series16_unit(mock_modbus_unit, mode)
    meter = await async_detect_meter(mock_modbus_unit)
    assert isinstance(meter, expected)
    assert meter.model == expected.model  # type: ignore[attr-defined]


async def test_detection_costs_one_read(mock_modbus_unit: MockModbusUnit) -> None:
    series16_unit(mock_modbus_unit, MeterMode.WSZ16D)
    await async_detect_meter(mock_modbus_unit)
    assert [(b.address, b.count) for b in mock_modbus_unit.read_events] == [(0xFC0C, 2)]


async def test_an_unknown_meter_mode_is_an_error(
    mock_modbus_unit: MockModbusUnit,
) -> None:
    series16_unit(mock_modbus_unit, 99)
    with pytest.raises(ValueError, match="meter mode 99"):
        await async_detect_meter(mock_modbus_unit)
