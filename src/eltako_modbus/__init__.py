"""eltako-modbus — read an Eltako energy meter over Modbus.

Construct the meter you have with a ``modbus_connection.ModbusUnit``, call
``await meter.async_update()``, then read the values as plain attributes::

    meter.measurements.voltage_l1
    meter.measurements.total_import_active_energy

There is a package per specification, because the two disagree — over the unit
of power, the baud-rate codes and the address range. The DSZ15DZMOD comes from
its own datasheet (V1.6, 06/2023) and has a package to itself; the six DSZ16
and WSZ16 meters share one register map, and so one package, from V3.7.4
(05/2026). Both documents are committed under ``docs/``; the README has the
differences. Where a name means one thing in each — ``BaudRate``, ``Identity``,
``Measurements``, ``Parameters`` — the DSZ15DZMOD's is re-exported here.

``async_detect_meter(unit)`` asks a meter which of the seven models it is and
hands back the object for it.
"""

from .detect import MODELS, EltakoMeter, async_detect_meter
from .dsz15dzmod import (
    ADDRESS_MAX,
    ADDRESS_MIN,
    MANUFACTURER,
    MODEL,
    BaudRate,
    Dsz15dzmod,
    Identity,
    Measurements,
    Parameters,
)
from .series16 import (
    Dsz16d,
    Dsz16dz,
    Dsz16wd,
    Dsz16wdz,
    MeterMode,
    Series16Meter,
    Wsz16d,
    Wsz16dz,
)

__all__ = [
    "ADDRESS_MAX",
    "ADDRESS_MIN",
    "MANUFACTURER",
    "MODEL",
    "MODELS",
    "BaudRate",
    "Dsz15dzmod",
    "Dsz16d",
    "Dsz16dz",
    "Dsz16wd",
    "Dsz16wdz",
    "EltakoMeter",
    "Identity",
    "Measurements",
    "MeterMode",
    "Parameters",
    "Series16Meter",
    "Wsz16d",
    "Wsz16dz",
    "async_detect_meter",
]
