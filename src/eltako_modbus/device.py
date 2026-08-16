"""The top-level DSZ15DZMOD device object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modbus_connection import (
    IllegalDataAddressError,
    IllegalFunctionError,
    ModbusConnectionError,
    ModbusError,
    ModbusTimeoutError,
)
from modbus_connection.model import Component

from .identity import Identity
from .measurements import Measurements
from .model import UpdateReport
from .parameters import Parameters

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

MANUFACTURER = "Eltako"
MODEL = "DSZ15DZMOD"

# What a poll refreshes. The settings are deliberately not in here: they change
# only when written, so a consumer that wants them updates ``parameters`` on its
# own schedule instead of paying for them every cycle.
_POLLED = ("measurements",)

# A block the meter answers for with one of these is simply not there; anything
# else (timeout, busy, dead link) means "not this time" and retries.
_ABSENT = (IllegalDataAddressError, IllegalFunctionError)


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
        self._polled: list[str] | None = None

    async def async_setup(self) -> None:
        """Read the identity block, which cannot change between polls.

        Run by the first :meth:`async_update` if the caller does not run it
        itself. A meter that refuses the block leaves the identity unread and
        the meter usable — the readings do not depend on it. Any other failure
        propagates and leaves the device unset up, so the next update retries.
        """
        try:
            await self.identity.async_update()
        except _ABSENT:
            pass
        self._polled = list(_POLLED)

    async def async_update(self) -> UpdateReport:
        """Refresh every polled sub-system, one at a time.

        A sub-system whose read fails keeps its previous values while the rest
        still refresh, and listeners fire only after every component has been
        tried. A failure of the link itself raises ``ModbusConnectionError``
        instead of reporting, and so does a timeout with nothing read yet: the
        meter is not answering, and the rest would only wait for their own
        timeouts. On a 9600-baud bus that is the difference between one wasted
        poll and a wedged link. The first call sets the device up.
        """
        if self._polled is None:
            await self.async_setup()
        assert self._polled is not None  # async_setup() builds it
        updated: set[str] = set()
        failed: dict[str, ModbusError] = {}
        for name in self._polled:
            component: Component = getattr(self, name)
            try:
                await component.async_update(notify=False)
            except ModbusConnectionError:
                raise
            except ModbusTimeoutError as err:
                if not updated and not failed:
                    raise  # nothing answered at all; assume the rest time out too
                failed[name] = err
            except ModbusError as err:
                failed[name] = err
            else:
                updated.add(name)
        for name in updated:
            fresh: Component = getattr(self, name)
            fresh.notify()
        return UpdateReport(updated, failed)

    async def async_read_raw(self) -> dict[str, dict[int, int | bool]]:
        """Every register this meter serves, undecoded — for diagnostics.

        The settings and the identity come along even though a poll skips them:
        a dump is read to find out how the meter is configured, and a refusal of
        the identity block is ordinary there as it is at setup. Setup is not
        needed — the polled set is the same on every DSZ15DZMOD — so this also
        works on a meter that never got that far. Nothing notifies: a download
        is not a poll.
        """
        raw: dict[str, dict[int, int | bool]] = {}
        try:
            reads = [await self.identity.async_read_raw(notify=False)]
        except _ABSENT:
            reads = []
        for name in (*_POLLED, "parameters"):
            component: Component = getattr(self, name)
            reads.append(await component.async_read_raw(notify=False))
        for read in reads:
            for space, values in read.items():
                raw.setdefault(space, {}).update(values)
        return {space: dict(sorted(values.items())) for space, values in raw.items()}
