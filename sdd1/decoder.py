from collections import namedtuple

from sdd1.errors import TruncatedStream

from .probability import (
    CONTEXT_COUNT,
    CONTEXT_MASKS,
    EVOLUTION,
    MAX_LENGTH,
    PLANE_COUNT,
    PREV_BITS_MASK,
    RUN_TABLE,
)

BITPLANE_COUNTS = (2, 4, 4, 8)

HEADER_BYTES = 2


Stream = namedtuple("Stream", "data end bitplanes context")


def bitplane_count(bitplane_type: int) -> int:
    return BITPLANE_COUNTS[bitplane_type]


def decompress(rom: bytes | bytearray, offset: int, length: int) -> "Stream":
    if length == 0:
        length = MAX_LENGTH
    if offset < 0 or offset + HEADER_BYTES > len(rom):
        raise TruncatedStream(offset)

    header = rom[offset]
    bitplane_type = header >> 6
    context_type = (header >> 4) & 3
    high_mask, low_mask = CONTEXT_MASKS[context_type]

    stream = ((header << 11) | (rom[offset + 1] << 3)) & 0xFFFF
    valid = 5
    pos = offset + HEADER_BYTES
    counters = [0] * PLANE_COUNT
    states = [0] * CONTEXT_COUNT
    mps = [0] * CONTEXT_COUNT
    prev = [0] * PLANE_COUNT
    out = bytearray()

    def get_bit(plane: int) -> int:
        nonlocal stream, valid, pos
        history = prev[plane]
        context = ((plane & 1) << 4) | ((history & high_mask) >> 5) | (history & low_mask)
        state = states[context]
        code_size, mps_next, lps_next = EVOLUTION[state]

        counter = counters[code_size]
        if counter == 0:
            if valid == 0:
                stream |= rom[pos]
                pos += 1
                valid = 8
            stream = ((stream << 1) & 0xFFFF) ^ 0x8000
            valid -= 1
            if stream & 0x8000:
                counter = (0x80 + (1 << code_size)) & 0xFF
            else:
                counter = RUN_TABLE[(stream >> 8) | (0x7F >> code_size)]
                stream = (stream << code_size) & 0xFFFF
                valid -= code_size
                if valid < 0:
                    stream |= rom[pos] << (-valid)
                    pos += 1
                    valid += 8

        counter = (counter - 1) & 0xFF
        if counter == 0x80:
            counters[code_size] = 0
            states[context] = mps_next
            bit = mps[context]
        elif counter == 0:
            counters[code_size] = 0
            states[context] = lps_next
            if state < 2:
                mps[context] ^= 1
                bit = mps[context]
            else:
                bit = mps[context] ^ 1
        else:
            counters[code_size] = counter
            bit = mps[context]

        prev[plane] = ((history << 1) | bit) & PREV_BITS_MASK
        return bit

    try:
        if bitplane_type == 3:
            while True:
                byte = 0
                for plane in range(PLANE_COUNT):
                    if get_bit(plane):
                        byte |= 1 << plane
                out.append(byte)
                length -= 1
                if length == 0:
                    break
        else:
            plane = 0
            step = 0
            while True:
                first = second = 0
                for shift in (7, 6, 5, 4, 3, 2, 1, 0):
                    if get_bit(plane):
                        first |= 1 << shift
                    if get_bit(plane + 1):
                        second |= 1 << shift
                out.append(first)
                length -= 1
                if length == 0:
                    break
                out.append(second)
                length -= 1
                if length == 0:
                    break
                step = (step + 32) & 0xFF
                if step == 0:
                    if bitplane_type == 1:
                        plane = (plane + 2) & 7
                    elif bitplane_type == 2:
                        plane ^= 2
    except IndexError:
        raise TruncatedStream(offset) from None

    return Stream(bytes(out), pos, bitplane_count(bitplane_type), context_type)
