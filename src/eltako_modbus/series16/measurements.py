"""What the meters measure — the input registers (FC04) of spec §3.1.

The seven models of the spec share one address map and differ only in which of
its rows they answer, so the layouts below are the map's four shapes: a
three-phase meter and a single-phase one, each with the export half of the map
added by the bidirectional ("Z") version. Each model reads only its own shape,
so a poll never asks for a register the model does not serve — and the
three-phase layouts pool into two block reads.

The transformer-connected DSZ16WD and DSZ16WDZ measure the same rows as the
directly connected DSZ16D and DSZ16DZ, but keep one decimal of energy instead
of two (Note 1), which no subclass can express by inheritance alone: their
energy fields are declared again at that scale.

Names keep the spec's wording. Voltages are line-to-neutral unless the name
says otherwise.
"""

from __future__ import annotations

from modbus_connection.model import Component, NumberField, enum

from .enums import Tariff
from .model import (
    CT_ENERGY_SCALE,
    ENERGY_SCALE,
    energy,
    power,
    power_factor,
    scaled,
)


class ThreePhaseMeasurements(Component):
    """Everything a DSZ16D measures."""

    register_space = "input"

    voltage_l1 = scaled(0x0000, unit="V")
    voltage_l2 = scaled(0x0002, unit="V")
    voltage_l3 = scaled(0x0004, unit="V")

    current_l1 = scaled(0x0006, unit="A")
    current_l2 = scaled(0x0008, unit="A")
    current_l3 = scaled(0x000A, unit="A")

    active_power_l1 = power(0x000C, unit="W")
    active_power_l2 = power(0x000E, unit="W")
    active_power_l3 = power(0x0010, unit="W")

    apparent_power_l1 = power(0x0012, unit="VA")
    apparent_power_l2 = power(0x0014, unit="VA")
    apparent_power_l3 = power(0x0016, unit="VA")

    reactive_power_l1 = power(0x0018, unit="var")
    reactive_power_l2 = power(0x001A, unit="var")
    reactive_power_l3 = power(0x001C, unit="var")

    power_factor_l1 = power_factor(0x001E)
    power_factor_l2 = power_factor(0x0020)
    power_factor_l3 = power_factor(0x0022)

    cos_phi_l1 = power_factor(0x0024)
    cos_phi_l2 = power_factor(0x0026)
    cos_phi_l3 = power_factor(0x0028)

    total_active_power = power(0x0034, unit="W")
    total_apparent_power = power(0x0036, unit="VA")
    total_reactive_power = power(0x0038, unit="var")

    total_power_factor = power_factor(0x003E)
    total_cos_phi = power_factor(0x0040)

    frequency = scaled(0x0046, unit="Hz")
    """The Remarks' two decimals. The data-format column says ``000000XX``,
    which would be two digits and no room for a mains frequency; the two
    disagree and the Remarks are the rule the rest of the map follows."""

    total_import_active_energy = energy(0x0048, ENERGY_SCALE)

    neutral_current = scaled(0x0050, unit="A")

    total_positive_reactive_energy = energy(0x0052, ENERGY_SCALE, unit="kvarh")

    voltage_l1_l2 = scaled(0x0056, unit="V")
    voltage_l2_l3 = scaled(0x0058, unit="V")
    voltage_l3_l1 = scaled(0x005A, unit="V")

    resettable_total_import_active_energy = energy(0x0060, ENERGY_SCALE)

    tariff_1_import_active_energy = energy(0x0064, ENERGY_SCALE)
    tariff_1_resettable_import_active_energy = energy(0x0066, ENERGY_SCALE)
    tariff_2_import_active_energy = energy(0x006C, ENERGY_SCALE)
    tariff_2_resettable_import_active_energy = energy(0x006E, ENERGY_SCALE)
    tariff_3_import_active_energy = energy(0x0074, ENERGY_SCALE)
    tariff_3_resettable_import_active_energy = energy(0x0076, ENERGY_SCALE)
    tariff_4_import_active_energy = energy(0x0084, ENERGY_SCALE)
    tariff_4_resettable_import_active_energy = energy(0x0086, ENERGY_SCALE)

    import_active_energy_l1 = energy(0x008C, ENERGY_SCALE)
    import_active_energy_l2 = energy(0x008E, ENERGY_SCALE)
    import_active_energy_l3 = energy(0x0090, ENERGY_SCALE)

    selected_tariff: NumberField[Tariff] = enum(0x0098, Tariff, count=2)
    """The tariff in force, decoded from the raw 1-4 the spec's own table
    gives. The Remarks' "two decimals" rule would make that 100-400 instead;
    the table is the more specific statement, so it wins here."""


class ThreePhaseBidirectionalMeasurements(ThreePhaseMeasurements):
    """A DSZ16DZ: a DSZ16D that also counts what flows the other way."""

    total_export_active_energy = energy(0x004A, ENERGY_SCALE)
    total_negative_reactive_energy = energy(0x0054, ENERGY_SCALE, unit="kvarh")

    resettable_total_export_active_energy = energy(0x0062, ENERGY_SCALE)

    tariff_1_export_active_energy = energy(0x0068, ENERGY_SCALE)
    tariff_1_resettable_export_active_energy = energy(0x006A, ENERGY_SCALE)
    tariff_2_export_active_energy = energy(0x0070, ENERGY_SCALE)
    tariff_2_resettable_export_active_energy = energy(0x0072, ENERGY_SCALE)
    tariff_3_export_active_energy = energy(0x0078, ENERGY_SCALE)
    tariff_3_resettable_export_active_energy = energy(0x007A, ENERGY_SCALE)
    tariff_4_export_active_energy = energy(0x0088, ENERGY_SCALE)
    tariff_4_resettable_export_active_energy = energy(0x008A, ENERGY_SCALE)

    export_active_energy_l1 = energy(0x0092, ENERGY_SCALE)
    export_active_energy_l2 = energy(0x0094, ENERGY_SCALE)
    export_active_energy_l3 = energy(0x0096, ENERGY_SCALE)


class TransformerMeasurements(ThreePhaseMeasurements):
    """A DSZ16WD: the DSZ16D map with one decimal of energy (Note 1)."""

    total_import_active_energy = energy(0x0048, CT_ENERGY_SCALE)
    total_positive_reactive_energy = energy(0x0052, CT_ENERGY_SCALE, unit="kvarh")
    resettable_total_import_active_energy = energy(0x0060, CT_ENERGY_SCALE)
    tariff_1_import_active_energy = energy(0x0064, CT_ENERGY_SCALE)
    tariff_1_resettable_import_active_energy = energy(0x0066, CT_ENERGY_SCALE)
    tariff_2_import_active_energy = energy(0x006C, CT_ENERGY_SCALE)
    tariff_2_resettable_import_active_energy = energy(0x006E, CT_ENERGY_SCALE)
    tariff_3_import_active_energy = energy(0x0074, CT_ENERGY_SCALE)
    tariff_3_resettable_import_active_energy = energy(0x0076, CT_ENERGY_SCALE)
    tariff_4_import_active_energy = energy(0x0084, CT_ENERGY_SCALE)
    tariff_4_resettable_import_active_energy = energy(0x0086, CT_ENERGY_SCALE)
    import_active_energy_l1 = energy(0x008C, CT_ENERGY_SCALE)
    import_active_energy_l2 = energy(0x008E, CT_ENERGY_SCALE)
    import_active_energy_l3 = energy(0x0090, CT_ENERGY_SCALE)


class TransformerBidirectionalMeasurements(TransformerMeasurements):
    """A DSZ16WDZ: the DSZ16DZ map, its energy at one decimal too."""

    total_export_active_energy = energy(0x004A, CT_ENERGY_SCALE)
    total_negative_reactive_energy = energy(0x0054, CT_ENERGY_SCALE, unit="kvarh")

    resettable_total_export_active_energy = energy(0x0062, CT_ENERGY_SCALE)

    tariff_1_export_active_energy = energy(0x0068, CT_ENERGY_SCALE)
    tariff_1_resettable_export_active_energy = energy(0x006A, CT_ENERGY_SCALE)
    tariff_2_export_active_energy = energy(0x0070, CT_ENERGY_SCALE)
    tariff_2_resettable_export_active_energy = energy(0x0072, CT_ENERGY_SCALE)
    tariff_3_export_active_energy = energy(0x0078, CT_ENERGY_SCALE)
    tariff_3_resettable_export_active_energy = energy(0x007A, CT_ENERGY_SCALE)
    tariff_4_export_active_energy = energy(0x0088, CT_ENERGY_SCALE)
    tariff_4_resettable_export_active_energy = energy(0x008A, CT_ENERGY_SCALE)

    export_active_energy_l1 = energy(0x0092, CT_ENERGY_SCALE)
    export_active_energy_l2 = energy(0x0094, CT_ENERGY_SCALE)
    export_active_energy_l3 = energy(0x0096, CT_ENERGY_SCALE)


class SinglePhaseMeasurements(Component):
    """Everything a WSZ16D measures.

    The rows it shares with the three-phase meters keep their addresses and
    their ``_l1`` names — the spec's own wording for the one phase it has —
    but it serves far fewer of them, so this is a layout of its own rather
    than a narrowing of :class:`ThreePhaseMeasurements`. It has no cosφ per
    phase, no neutral current, no line-to-line voltage, no per-phase energy
    and no tariffs 3 and 4.
    """

    register_space = "input"

    voltage_l1 = scaled(0x0000, unit="V")
    current_l1 = scaled(0x0006, unit="A")
    active_power_l1 = power(0x000C, unit="W")
    apparent_power_l1 = power(0x0012, unit="VA")
    reactive_power_l1 = power(0x0018, unit="var")
    power_factor_l1 = power_factor(0x001E)

    total_active_power = power(0x0034, unit="W")
    total_apparent_power = power(0x0036, unit="VA")
    total_reactive_power = power(0x0038, unit="var")

    total_power_factor = power_factor(0x003E)
    total_cos_phi = power_factor(0x0040)

    frequency = scaled(0x0046, unit="Hz")

    total_import_active_energy = energy(0x0048, ENERGY_SCALE)
    total_positive_reactive_energy = energy(0x0052, ENERGY_SCALE, unit="kvarh")

    resettable_total_import_active_energy = energy(0x0060, ENERGY_SCALE)

    tariff_1_import_active_energy = energy(0x0064, ENERGY_SCALE)
    tariff_1_resettable_import_active_energy = energy(0x0066, ENERGY_SCALE)
    tariff_2_import_active_energy = energy(0x006C, ENERGY_SCALE)
    tariff_2_resettable_import_active_energy = energy(0x006E, ENERGY_SCALE)

    selected_tariff: NumberField[Tariff] = enum(0x0098, Tariff, count=2)


class SinglePhaseBidirectionalMeasurements(SinglePhaseMeasurements):
    """A WSZ16DZ: a WSZ16D that also counts what flows the other way."""

    total_export_active_energy = energy(0x004A, ENERGY_SCALE)
    total_negative_reactive_energy = energy(0x0054, ENERGY_SCALE, unit="kvarh")

    resettable_total_export_active_energy = energy(0x0062, ENERGY_SCALE)

    tariff_1_export_active_energy = energy(0x0068, ENERGY_SCALE)
    tariff_1_resettable_export_active_energy = energy(0x006A, ENERGY_SCALE)
    tariff_2_export_active_energy = energy(0x0070, ENERGY_SCALE)
    tariff_2_resettable_export_active_energy = energy(0x0072, ENERGY_SCALE)
