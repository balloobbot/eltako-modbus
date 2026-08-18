"""Packed BCD — the one codec both of Eltako's specifications share.

Each document states the serial number at 0xFC00 as eight BCD digits, in the
same place and the same encoding, so this sits above the two device packages
rather than in either of them.
"""

from __future__ import annotations


def bcd_digits(raw: int) -> str:
    """Decode a packed-BCD word into its digits; a nibble above 9 is not BCD."""
    digits = f"{raw:08x}"
    if not digits.isdigit():
        raise ValueError(f"not packed BCD: 0x{raw:08X}")
    return digits
