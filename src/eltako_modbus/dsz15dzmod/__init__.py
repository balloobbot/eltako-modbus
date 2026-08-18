"""The Eltako DSZ15DZMOD three-phase energy meter.

Transcribed from *Modbus-RTU protocol specification for DSZ15DZMOD V1.6*
(06/2023), committed under ``docs/``. That document disagrees with the later
V3.7.4 specification about this meter's unit of power, its baud-rate codes and
its address range, so nothing here is shared with
:mod:`eltako_modbus.series16`; the README has the differences.
"""

from .device import MANUFACTURER, MODEL, Dsz15dzmod
from .enums import BaudRate
from .identity import Identity
from .measurements import Measurements
from .parameters import ADDRESS_MAX, ADDRESS_MIN, Parameters

__all__ = [
    "ADDRESS_MAX",
    "ADDRESS_MIN",
    "MANUFACTURER",
    "MODEL",
    "BaudRate",
    "Dsz15dzmod",
    "Identity",
    "Measurements",
    "Parameters",
]
