"""Field presets for the DSZ15DZMOD's uniform 32-bit layout, and the poll report.

Every value the meter exposes — measurement or parameter — is 4 bytes across two
consecutive registers, high word in the lower address (spec §1.2.2 and §3.1
remark 2). That is ``count=2`` with the default ``word_order="big"``, so the
helpers below spell out only what differs between the three scaling rules the
spec states in §3.1 remark 1.
"""

from __future__ import annotations

from dataclasses import dataclass

from modbus_connection import ModbusError
from modbus_connection.model import NumberField, WriteValidator


def scaled(address: int, *, unit: str) -> NumberField[float]:
    """An unsigned measurement with two decimals — the spec's default rule."""
    return NumberField[float](address, count=2, scale=0.01, signed=False, unit=unit)


def power(address: int) -> NumberField[int]:
    """A signed active-power measurement, in whole kW as the spec states.

    The spec gives power a unit of kW, signed, and — alone among the
    measurements — *no* decimals, which makes the step 1 kW. That is hard to
    believe from a meter that reports *energy* to two decimals, 10 Wh: the same
    device would resolve accumulated energy a hundred thousand times finer than
    the power producing it. The likeliest explanation is that the raw value is
    watts and the unit column is wrong, but the spec says what it says and
    nothing here can settle it without hardware. So this models the datasheet
    exactly and hands back the raw integer unscaled; a consumer that measures
    otherwise can divide. See the README.
    """
    return NumberField[int](address, count=2, signed=True, unit="kW")


def power_factor(address: int) -> NumberField[float]:
    """A signed power factor with three decimals."""
    return NumberField[float](address, count=2, scale=0.001, signed=True)


def unscaled(
    address: int, *, writable: bool | WriteValidator = False
) -> NumberField[int]:
    """An unsigned parameter word, read as-is.

    §3.1's scaling remarks cover the measurements only; the parameter table
    states no scale and every documented value is a small count or code.
    """
    return NumberField[int](address, count=2, signed=False, writable=writable)


@dataclass(frozen=True)
class UpdateReport:
    """What one poll refreshed, by the device's component attribute names.

    A failed component kept its previous values and did not notify; the error
    that failed it rides along. A dead link is never in here — the update
    raises ``ModbusConnectionError`` instead of reporting partial silence.
    """

    updated: set[str]
    failed: dict[str, ModbusError]

    @property
    def complete(self) -> bool:
        """Whether every polled component refreshed."""
        return not self.failed
