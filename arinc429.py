"""ARINC 429 word construction for a documented, deliberately simple profile.

This module builds the 32-bit logical word. It does not implement the ARINC
429 electrical layer or replace a certified bus interface.
"""

from dataclasses import dataclass
import math

WORD_MASK = 0xFFFFFFFF
DATA_MASK = (1 << 19) - 1


@dataclass(frozen=True)
class WordFields:
    label_octal: str
    sdi: int
    data: int
    ssm: int


def _label_value(label_octal: str) -> int:
    value = int(label_octal, 8)
    if not 0 <= value <= 0xFF:
        raise ValueError("La etiqueta octal debe representar un valor de 8 bits.")
    return value


def reverse_bits(value: int, width: int) -> int:
    result = 0
    for bit in range(width):
        result = (result << 1) | ((value >> bit) & 1)
    return result


def encode_data(value: float, encoding: str, resolution: float) -> int:
    if not math.isfinite(value) or not math.isfinite(resolution) or resolution <= 0:
        raise ValueError("El valor y la resolución deben ser finitos; resolución > 0.")
    scaled = value / resolution
    if not math.isclose(scaled, round(scaled), rel_tol=0.0, abs_tol=1e-8):
        raise ValueError("El valor no es múltiplo de la resolución configurada.")
    integer = int(round(scaled))
    if encoding == "BNR":
        if not -(1 << 18) <= integer < (1 << 18):
            raise ValueError("El dato BNR excede el rango de 19 bits con signo.")
        return integer & DATA_MASK
    if encoding == "UINT":
        if not 0 <= integer <= DATA_MASK:
            raise ValueError("El dato UINT debe caber en 19 bits sin signo.")
        return integer
    raise ValueError("Codificación no soportada; use BNR o UINT.")


def build_word(label_octal: str, sdi: int, data: int, ssm: int) -> int:
    """Build a 32-bit word: reversed label, SDI, 19 data bits, SSM, odd parity."""
    if not 0 <= sdi <= 3:
        raise ValueError("SDI debe estar entre 0 y 3.")
    if not 0 <= ssm <= 3:
        raise ValueError("SSM debe estar entre 0 y 3.")
    if not 0 <= data <= DATA_MASK:
        raise ValueError("El campo de datos debe caber en 19 bits.")

    label = reverse_bits(_label_value(label_octal), 8)
    word = label | (sdi << 8) | (data << 10) | (ssm << 29)
    # The parity bit makes the total number of 1 bits odd.
    if word.bit_count() % 2 == 0:
        word |= 1 << 31
    return word & WORD_MASK


def word_hex(word: int) -> str:
    if not 0 <= word <= WORD_MASK:
        raise ValueError("La palabra debe ser un entero de 32 bits.")
    return f"0x{word:08X}"
