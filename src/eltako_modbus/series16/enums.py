"""Coded values of the DSZ16/WSZ16 register map (spec §3.1 and §3.2)."""

from __future__ import annotations

from enum import IntEnum


class MeterMode(IntEnum):
    """Which meter this is, from 0xFC0C — the one register that names the model."""

    NOT_APPLICABLE = 0
    DSZ15DZMOD = 1
    DSZ16D = 2
    DSZ16DZ = 3
    DSZ16WD = 4
    DSZ16WDZ = 5
    WSZ16D = 6
    WSZ16DZ = 7


class SerialFormat(IntEnum):
    """Parity and stop bits of parameter 0x0012, default 0."""

    ONE_STOP_NO_PARITY = 0
    ONE_STOP_EVEN_PARITY = 1
    ONE_STOP_ODD_PARITY = 2
    TWO_STOP_NO_PARITY = 3


class BaudRate(IntEnum):
    """The link speed of parameter 0x001C, default 9600 bit/s."""

    BPS_300 = 0
    BPS_600 = 1
    BPS_1200 = 2
    BPS_2400 = 3
    BPS_4800 = 4
    BPS_9600 = 5
    BPS_14400 = 6
    BPS_19200 = 7
    BPS_38400 = 8
    BPS_57600 = 9
    BPS_115200 = 0x0A


class DataFormat(IntEnum):
    """How parameter 0x001E has the meter encode its measurements.

    This library decodes ``INTEGER``, the default. A meter switched to
    ``FLOAT`` answers the same registers with IEEE-754 words, which every
    field here would decode as a nonsense integer — the spec does not
    document that encoding's word order, so it is not modelled.
    """

    INTEGER = 0
    FLOAT = 1


class Tariff(IntEnum):
    """The tariff in force, from 0x0098. Tariffs 3 and 4 are DSZ16-only."""

    TARIFF_1 = 1
    TARIFF_2 = 2
    TARIFF_3 = 3
    TARIFF_4 = 4


class TariffSelection(IntEnum):
    """What selects the tariff, parameter 0x005A.

    ``EXTERNAL`` leaves it to the E2/E3/E4 control wiring. A tariff picked
    here holds only while those terminals stay disconnected: the spec states
    that the wiring takes priority over the register.
    """

    EXTERNAL = 0
    TARIFF_1 = 1
    TARIFF_2 = 2
    TARIFF_3 = 3
    TARIFF_4 = 4


class PulseConstant(IntEnum):
    """Pulses per kWh on an S0 output (parameters 0xF910 and 0xF912).

    The default is 1000 imp/kWh on a directly connected meter and 10 imp/kWh
    on a transformer-connected one.
    """

    NOT_APPLICABLE = 0
    IMP_0_01_PER_KWH = 1
    IMP_0_1_PER_KWH = 2
    IMP_1_PER_KWH = 3
    IMP_10_PER_KWH = 4
    IMP_100_PER_KWH = 5
    IMP_1000_PER_KWH = 6
    IMP_2000_PER_KWH = 7
    IMP_10000_PER_KWH = 8


class CtRatio(IntEnum):
    """The current-transformer ratio of parameter 0xF914, default 5:5.

    Codes 1-0x0E are the ratios onto a 5 A secondary, 0x0F-0x1C the same
    primaries onto a 1 A one.
    """

    NOT_APPLICABLE = 0
    RATIO_5_5 = 1
    RATIO_50_5 = 2
    RATIO_100_5 = 3
    RATIO_150_5 = 4
    RATIO_200_5 = 5
    RATIO_250_5 = 6
    RATIO_300_5 = 7
    RATIO_400_5 = 8
    RATIO_500_5 = 9
    RATIO_600_5 = 0x0A
    RATIO_750_5 = 0x0B
    RATIO_1000_5 = 0x0C
    RATIO_1250_5 = 0x0D
    RATIO_1500_5 = 0x0E
    RATIO_5_1 = 0x0F
    RATIO_50_1 = 0x10
    RATIO_100_1 = 0x11
    RATIO_150_1 = 0x12
    RATIO_200_1 = 0x13
    RATIO_250_1 = 0x14
    RATIO_300_1 = 0x15
    RATIO_400_1 = 0x16
    RATIO_500_1 = 0x17
    RATIO_600_1 = 0x18
    RATIO_750_1 = 0x19
    RATIO_1000_1 = 0x1A
    RATIO_1250_1 = 0x1B
    RATIO_1500_1 = 0x1C
