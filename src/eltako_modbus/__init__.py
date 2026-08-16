"""eltako-modbus — read an Eltako DSZ15DZMOD energy meter over Modbus RTU.

Construct ``Dsz15dzmod(unit)`` with a ``modbus_connection.ModbusUnit``, call
``await meter.async_update()``, then read the values as plain attributes::

    meter.measurements.voltage_l1
    meter.measurements.total_import_active_energy

The register map is transcribed from Eltako's *Modbus-RTU protocol
specification for DSZ15DZMOD V1.6* (06/2023), a copy of which is committed
under ``docs/``. Active power is modelled exactly as that document states it —
see the README before trusting its scale.
"""

from .device import MANUFACTURER, MODEL, Dsz15dzmod
from .enums import BaudRate
from .identity import SERIAL_ADDRESS, Identity
from .measurements import Measurements
from .parameters import ADDRESS_MAX, ADDRESS_MIN, Parameters

__all__ = [
    "ADDRESS_MAX",
    "ADDRESS_MIN",
    "MANUFACTURER",
    "MODEL",
    "SERIAL_ADDRESS",
    "BaudRate",
    "Dsz15dzmod",
    "Identity",
    "Measurements",
    "Parameters",
]
