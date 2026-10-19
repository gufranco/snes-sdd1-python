from collections import namedtuple
from collections.abc import Callable

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

EIGHT_PLANES = 3

ROTATE_BY_TWO = 1

ROTATE_BY_TOGGLE = 2

PAIR_STEP = 32

BYTE_MASK = 0xFF

STREAM_MASK = 0xFFFF

LEADING_BIT = 0x8000

Stream = namedtuple("Stream", "data end bitplanes context")


def bitplane_count(bitplane_type: int) -> int:
    return BITPLANE_COUNTS[bitplane_type]


class Expansion:
    __slots__ = (
        "context",
        "counters",
        "fetch",
        "high_mask",
        "history",
        "kind",
        "likely",
        "low_mask",
        "pending",
        "plane",
        "position",
        "states",
        "step",
        "stream",
        "valid",
    )

    def __init__(self, fetch: Callable[[int], int], offset: int) -> None:
        header = fetch(offset)
        self.fetch = fetch
        self.kind = header >> 6
        self.context = (header >> 4) & 3
        self.high_mask, self.low_mask = CONTEXT_MASKS[self.context]
        self.stream = ((header << 11) | (fetch(offset + 1) << 3)) & STREAM_MASK
        self.valid = 5
        self.position = offset + HEADER_BYTES
        self.counters = [0] * PLANE_COUNT
        self.states = [0] * CONTEXT_COUNT
        self.likely = [0] * CONTEXT_COUNT
        self.history = [0] * PLANE_COUNT
        self.plane = 0
        self.step = 0
        self.pending: int | None = None

    def _take(self) -> int:
        value = self.fetch(self.position)
        self.position += 1
        return value

    def _run(self, code_size: int) -> int:
        if self.valid == 0:
            self.stream |= self._take()
            self.valid = 8
        self.stream = ((self.stream << 1) & STREAM_MASK) ^ LEADING_BIT
        self.valid -= 1
        if self.stream & LEADING_BIT:
            return (0x80 + (1 << code_size)) & BYTE_MASK
        counter = RUN_TABLE[(self.stream >> 8) | (0x7F >> code_size)]
        self.stream = (self.stream << code_size) & STREAM_MASK
        self.valid -= code_size
        if self.valid < 0:
            self.stream |= self._take() << (-self.valid)
            self.valid += 8
        return counter

    def _decide(self, context: int, state: int, counter: int) -> int:
        code_size, likely_next, unlikely_next = EVOLUTION[state]
        if counter == 0x80:
            self.counters[code_size] = 0
            self.states[context] = likely_next
            return self.likely[context]
        if counter == 0:
            self.counters[code_size] = 0
            self.states[context] = unlikely_next
            if state < 2:
                self.likely[context] ^= 1
                return self.likely[context]
            return self.likely[context] ^ 1
        self.counters[code_size] = counter
        return self.likely[context]

    def _bit(self, plane: int) -> int:
        history = self.history[plane]
        context = ((plane & 1) << 4) | ((history & self.high_mask) >> 5) | (history & self.low_mask)
        state = self.states[context]
        code_size = EVOLUTION[state][0]
        counter = self.counters[code_size]
        if counter == 0:
            counter = self._run(code_size)
        bit = self._decide(context, state, (counter - 1) & BYTE_MASK)
        self.history[plane] = ((history << 1) | bit) & PREV_BITS_MASK
        return bit

    def _interleaved(self) -> int:
        value = 0
        for plane in range(PLANE_COUNT):
            if self._bit(plane):
                value |= 1 << plane
        return value

    def _rotate(self) -> None:
        self.step = (self.step + PAIR_STEP) & BYTE_MASK
        if self.step != 0:
            return
        if self.kind == ROTATE_BY_TWO:
            self.plane = (self.plane + 2) & 7
        elif self.kind == ROTATE_BY_TOGGLE:
            self.plane ^= 2

    def _pair(self) -> int:
        first = second = 0
        for shift in (7, 6, 5, 4, 3, 2, 1, 0):
            if self._bit(self.plane):
                first |= 1 << shift
            if self._bit(self.plane + 1):
                second |= 1 << shift
        self.pending = second
        return first

    def byte(self) -> int:
        if self.kind == EIGHT_PLANES:
            return self._interleaved()
        if self.pending is None:
            return self._pair()
        second = self.pending
        self.pending = None
        self._rotate()
        return second


def decompress(rom: bytes | bytearray, offset: int, length: int) -> "Stream":
    if length == 0:
        length = MAX_LENGTH
    if offset < 0 or offset + HEADER_BYTES > len(rom):
        raise TruncatedStream(offset)
    expansion = Expansion(rom.__getitem__, offset)
    try:
        data = bytes(expansion.byte() for _ in range(length))
    except IndexError:
        raise TruncatedStream(offset) from None
    return Stream(data, expansion.position, bitplane_count(expansion.kind), expansion.context)
