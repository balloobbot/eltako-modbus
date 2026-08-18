"""The six device objects of the DSZ16/WSZ16 family.

Each model is a name, a measurement layout, and the settings and counter
resets it serves — the Support columns of spec §3.1 and §3.2. The behaviour
around them is the same for all six, so it lives on the base class.

The spec's general note makes the non-MID variants the same meters: DSZ16DE
reads as DSZ16D, DSZ16DZE as DSZ16DZ, WSZ16DE as WSZ16D and WSZ16DZE as
WSZ16DZ.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from modbus_connection.model import Component

from .identity import Identity
from .measurements import (
    SinglePhaseBidirectionalMeasurements,
    SinglePhaseMeasurements,
    ThreePhaseBidirectionalMeasurements,
    ThreePhaseMeasurements,
    TransformerBidirectionalMeasurements,
    TransformerMeasurements,
)
from .parameters import (
    COMMON_PARAMETERS,
    COMMON_RESETS,
    EXPORT_PARAMETERS,
    EXPORT_RESETS,
    THREE_PHASE_EXPORT_RESETS,
    THREE_PHASE_PARAMETERS,
    THREE_PHASE_RESETS,
    TRANSFORMER_PARAMETERS,
    Parameters,
    Resets,
)

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

MANUFACTURER = "Eltako"


class Series16Meter[M: Component]:
    """An Eltako meter of the DSZ16/WSZ16 family, generic over what it measures.

    Takes a :class:`~modbus_connection.ModbusUnit`; the caller owns the
    connection, over a serial line or through a Modbus TCP gateway.
    """

    manufacturer = MANUFACTURER
    model: ClassVar[str]
    parameter_fields: ClassVar[tuple[str, ...]]
    reset_fields: ClassVar[tuple[str, ...]]

    def __init__(self, unit: ModbusUnit, measurements: M) -> None:
        self._unit = unit
        self.measurements = measurements
        self.identity = Identity(unit)
        self.parameters = Parameters(unit)
        self.parameters.restrict_fields(self.parameter_fields)
        self.resets = Resets(unit)
        self.resets.restrict_fields(self.reset_fields)
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
        """Every register this meter is read from, undecoded — for diagnostics.

        The identity and the settings come along even though a poll skips them:
        a dump is read to find out how the meter is configured. The counter
        resets stay out — they are written, never read. Nothing notifies: a
        download is not a poll.
        """
        raw: dict[str, dict[int, int | bool]] = {}
        for component in (self.identity, self.parameters, self.measurements):
            for space, values in (await component.async_read_raw(notify=False)).items():
                raw.setdefault(space, {}).update(values)
        return {space: dict(sorted(values.items())) for space, values in raw.items()}


class Dsz16d(Series16Meter[ThreePhaseMeasurements]):
    """A DSZ16D three-phase meter, direct connection, one direction."""

    model = "DSZ16D"
    parameter_fields = COMMON_PARAMETERS + THREE_PHASE_PARAMETERS
    reset_fields = COMMON_RESETS + THREE_PHASE_RESETS

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit, ThreePhaseMeasurements(unit))


class Dsz16dz(Series16Meter[ThreePhaseBidirectionalMeasurements]):
    """A DSZ16DZ three-phase meter, direct connection, both directions."""

    model = "DSZ16DZ"
    parameter_fields = COMMON_PARAMETERS + EXPORT_PARAMETERS + THREE_PHASE_PARAMETERS
    reset_fields = (
        COMMON_RESETS + EXPORT_RESETS + THREE_PHASE_RESETS + THREE_PHASE_EXPORT_RESETS
    )

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit, ThreePhaseBidirectionalMeasurements(unit))


class Dsz16wd(Series16Meter[TransformerMeasurements]):
    """A DSZ16WD three-phase meter, transformer connection, one direction."""

    model = "DSZ16WD"
    parameter_fields = (
        COMMON_PARAMETERS + THREE_PHASE_PARAMETERS + TRANSFORMER_PARAMETERS
    )
    reset_fields = COMMON_RESETS + THREE_PHASE_RESETS

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit, TransformerMeasurements(unit))


class Dsz16wdz(Series16Meter[TransformerBidirectionalMeasurements]):
    """A DSZ16WDZ three-phase meter, transformer connection, both directions."""

    model = "DSZ16WDZ"
    parameter_fields = (
        COMMON_PARAMETERS
        + EXPORT_PARAMETERS
        + THREE_PHASE_PARAMETERS
        + TRANSFORMER_PARAMETERS
    )
    reset_fields = (
        COMMON_RESETS + EXPORT_RESETS + THREE_PHASE_RESETS + THREE_PHASE_EXPORT_RESETS
    )

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit, TransformerBidirectionalMeasurements(unit))


class Wsz16d(Series16Meter[SinglePhaseMeasurements]):
    """A WSZ16D single-phase meter, one direction."""

    model = "WSZ16D"
    parameter_fields = COMMON_PARAMETERS
    reset_fields = COMMON_RESETS

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit, SinglePhaseMeasurements(unit))


class Wsz16dz(Series16Meter[SinglePhaseBidirectionalMeasurements]):
    """A WSZ16DZ single-phase meter, both directions."""

    model = "WSZ16DZ"
    parameter_fields = COMMON_PARAMETERS + EXPORT_PARAMETERS
    reset_fields = COMMON_RESETS + EXPORT_RESETS

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit, SinglePhaseBidirectionalMeasurements(unit))
