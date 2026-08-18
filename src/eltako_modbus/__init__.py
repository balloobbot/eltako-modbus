"""eltako-modbus — read an Eltako energy meter over Modbus.

Construct the meter you have with a ``modbus_connection.ModbusUnit``, call
``await meter.async_update()``, then read the values as plain attributes::

    meter.measurements.voltage_l1
    meter.measurements.total_import_active_energy

``Dsz15dzmod`` is transcribed from Eltako's *Modbus-RTU protocol specification
for DSZ15DZMOD V1.6* (06/2023). The DSZ16 and WSZ16 meters come from the
*Modbus-RTU protocol specification V3.7.4* (05/2026), and live in
:mod:`eltako_modbus.series16` because the two documents disagree — over the
unit of power, the baud-rate codes and the address range. Both are committed
under ``docs/``; the README has the differences.

``async_detect_meter(unit)`` asks a meter which of the seven models it is and
hands back the object for it.
"""

from .detect import MODELS, EltakoMeter, async_detect_meter
from .device import MANUFACTURER, MODEL, Dsz15dzmod
from .enums import BaudRate
from .identity import Identity
from .measurements import Measurements
from .parameters import ADDRESS_MAX, ADDRESS_MIN, Parameters
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
