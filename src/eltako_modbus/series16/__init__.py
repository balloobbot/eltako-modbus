"""The DSZ16 and WSZ16 meters of Eltako's *Modbus-RTU protocol specification*.

Six models share one register map: the three-phase DSZ16D and DSZ16DZ, the
transformer-connected DSZ16WD and DSZ16WDZ, and the single-phase WSZ16D and
WSZ16DZ. Construct the one you have with a ``modbus_connection.ModbusUnit``,
call ``await meter.async_update()``, then read the values as plain attributes::

    meter = Dsz16dz(unit)
    await meter.async_update()
    meter.measurements.voltage_l1
    meter.measurements.total_export_active_energy

The map is transcribed from *Modbus-RTU protocol specification V3.7.4*
(05/2026), committed under ``docs/``. Its codes and units differ from the
DSZ15DZMOD's own datasheet in places, so nothing here is shared with
:class:`~eltako_modbus.Dsz15dzmod`; the differences are in the README.
"""

from .device import (
    MANUFACTURER,
    Dsz16d,
    Dsz16dz,
    Dsz16wd,
    Dsz16wdz,
    Series16Meter,
    Wsz16d,
    Wsz16dz,
)
from .enums import (
    BaudRate,
    CtRatio,
    DataFormat,
    MeterMode,
    PulseConstant,
    SerialFormat,
    Tariff,
    TariffSelection,
)
from .identity import Identity
from .measurements import (
    SinglePhaseBidirectionalMeasurements,
    SinglePhaseMeasurements,
    ThreePhaseBidirectionalMeasurements,
    ThreePhaseMeasurements,
    TransformerBidirectionalMeasurements,
    TransformerMeasurements,
)
from .parameters import ADDRESS_MAX, ADDRESS_MIN, Parameters, Resets

__all__ = [
    "ADDRESS_MAX",
    "ADDRESS_MIN",
    "MANUFACTURER",
    "BaudRate",
    "CtRatio",
    "DataFormat",
    "Dsz16d",
    "Dsz16dz",
    "Dsz16wd",
    "Dsz16wdz",
    "Identity",
    "MeterMode",
    "Parameters",
    "PulseConstant",
    "Resets",
    "SerialFormat",
    "Series16Meter",
    "SinglePhaseBidirectionalMeasurements",
    "SinglePhaseMeasurements",
    "Tariff",
    "TariffSelection",
    "ThreePhaseBidirectionalMeasurements",
    "ThreePhaseMeasurements",
    "TransformerBidirectionalMeasurements",
    "TransformerMeasurements",
    "Wsz16d",
    "Wsz16dz",
]
