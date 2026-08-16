"""Coded parameter values.

Only the baud-rate codes are stated unambiguously enough to enumerate; see
:class:`~eltako_modbus.parameters.Parameters` for the ones that are not.
"""

from __future__ import annotations

from enum import IntEnum


class BaudRate(IntEnum):
    """The baud-rate codes of parameter 0x001C. Code 4 is not assigned."""

    BPS_2400 = 0
    BPS_4800 = 1
    BPS_9600 = 2
    BPS_19200 = 3
    BPS_1200 = 5
