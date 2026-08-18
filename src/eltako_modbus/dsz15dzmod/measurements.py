"""The meter's readings — the whole of the input-register space (FC04).

The DSZ15DZMOD has one measurement block and no optional parts, so this is a
single component rather than a phase/total/energy split: the values share a
space, are always all present, and cannot fail independently of one another.
Splitting them would only buy extra round trips on a slow serial line.

Addresses and units are spec §3.1; names keep the spec's wording. Voltages are
line-to-neutral.
"""

from __future__ import annotations

from modbus_connection.model import Component

from .model import power, power_factor, scaled


class Measurements(Component):
    """Everything the meter measures, read from the input registers."""

    register_space = "input"

    voltage_l1 = scaled(0x0000, unit="V")
    voltage_l2 = scaled(0x0002, unit="V")
    voltage_l3 = scaled(0x0004, unit="V")

    current_l1 = scaled(0x0006, unit="A")
    current_l2 = scaled(0x0008, unit="A")
    current_l3 = scaled(0x000A, unit="A")

    active_power_l1 = power(0x000C)
    active_power_l2 = power(0x000E)
    active_power_l3 = power(0x0010)

    power_factor_l1 = power_factor(0x001E)
    power_factor_l2 = power_factor(0x0020)
    power_factor_l3 = power_factor(0x0022)

    total_active_power = power(0x0034)
    total_power_factor = power_factor(0x003E)

    total_import_active_energy = scaled(0x0048, unit="kWh")
    total_export_active_energy = scaled(0x004A, unit="kWh")
    part_import_active_energy = scaled(0x0060, unit="kWh")
    part_export_active_energy = scaled(0x0062, unit="kWh")
