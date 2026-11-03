"""Opt-in transport for adapters that explicitly document raw 4-byte UART words.

This is NOT an ARINC 429 transmitter. UART framing, word byte order, electrical
levels and adapter commands must match the specific adapter documentation.
"""

import os


def transmit_raw_word(word: int) -> None:
    if os.getenv("HW_SERIAL_ENABLED") != "1" or os.getenv("HW_SERIAL_RAW_WORDS") != "1":
        raise RuntimeError("Transmisión deshabilitada: requiere HW_SERIAL_ENABLED=1 y HW_SERIAL_RAW_WORDS=1.")
    port = os.getenv("HW_SERIAL_PORT", "").strip()
    if not port:
        raise RuntimeError("Configure HW_SERIAL_PORT para el adaptador documentado.")
    try:
        baudrate = int(os.getenv("HW_SERIAL_BAUDRATE", "115200"))
    except ValueError as exc:
        raise RuntimeError("HW_SERIAL_BAUDRATE debe ser un entero.") from exc
    if not 0 <= word <= 0xFFFFFFFF:
        raise ValueError("La palabra debe ser de 32 bits.")

    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("pyserial no está instalado.") from exc
    # Big-endian here is only a placeholder transport convention; verify the
    # adapter's actual protocol before enabling physical transmission.
    with serial.Serial(port=port, baudrate=baudrate, timeout=1, write_timeout=1) as device:
        written = device.write(word.to_bytes(4, byteorder="big"))
        if written != 4:
            raise RuntimeError("El adaptador no aceptó los cuatro bytes completos.")
