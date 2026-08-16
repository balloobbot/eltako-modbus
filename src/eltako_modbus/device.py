"""The top-level DSZ15DZMOD device object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .identity import Identity
from .measurements import Measurements
from .parameters import Parameters

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

MANUFACTURER = "Eltako"
MODEL = "DSZ15DZMOD"


class Dsz15dzmod:
    """An Eltako DSZ15DZMOD three-phase energy meter.

    Takes a :class:`~modbus_connection.ModbusUnit`; the caller owns the
    connection. The meter speaks Modbus RTU at 9600 baud by default.
    """

    manufacturer = MANUFACTURER
    model = MODEL

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit
        self.measurements = Measurements(unit)
        self.parameters = Parameters(unit)
        self.identity = Identity(unit)
        self._read_once = False

    async def async_setup(self) -> None:
        """Read what cannot change between polls: the identity and the settings.

        Run by the first :meth:`async_update` if the caller does not run it
        itself. A failure leaves the device unset up, so the next update retries.
        """
        await self.identity.async_update()
        await self.parameters.async_update()
        self._read_once = True

    async def async_update(self) -> None:
        """Refresh the readings. The first call reads the fixed blocks too."""
        if not self._read_once:
            await self.async_setup()
        await self.measurements.async_update()

    async def async_read_raw(self) -> dict[str, dict[int, int | bool]]:
        """Every register this meter serves, undecoded — for diagnostics.

        The identity and the settings come along even though a poll skips them:
        a dump is read to find out how the meter is configured. Nothing
        notifies: a download is not a poll.
        """
        raw: dict[str, dict[int, int | bool]] = {}
        for component in (self.identity, self.parameters, self.measurements):
            for space, values in (await component.async_read_raw(notify=False)).items():
                raw.setdefault(space, {}).update(values)
        return {space: dict(sorted(values.items())) for space, values in raw.items()}
