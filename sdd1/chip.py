import random
from typing import Any, override

from sdd1.errors import EmptyRom, OutOfRange

from .decoder import Expansion, decompress

UNSET_SEED = 0x5DD1

ROM_BYTES = 0x400000

HARD_ENABLE = 0x4800

SOFT_ENABLE = 0x4801

FIRST_BANK = 0x4804

BANK_WRITE_MASK = 0x8F

BANK_NUMBER_MASK = 0x0F

LOROM_REMAP_BIT = 0x80

RESET_BANKS = (0, 1, 2, 3)

CHANNELS = 8

REGISTER_WINDOW = 0x4800

DMA_WINDOW = 0x4300

DMA_WINDOW_END = 0x437F

PROGRAM_WINDOW = 0x8000

MMC_FIRST_BANK = 0xC0

LOW_BANK_LIMIT = 0x40

MIRROR_BANK = 0x80

ADDRESS_MASK = 0xFFFFFF

MEGABYTE_SHIFT = 20

MEGABYTE_MASK = 0xFFFFF

UPPER_HALF = 0x200000

LOROM_PAGE_SHIFT = 15

LOROM_PAGE_MASK = 0x7FFF

SIZE_MASK = 0xFFFF

SNOOPED = {2: (0, 0), 3: (0, 8), 4: (0, 16), 5: (1, 0), 6: (1, 8)}


def _snooped(channel: tuple[int, int], register: int, value: int) -> tuple[int, int]:
    field, shift = SNOOPED[register]
    held = channel[field] & ~(0xFF << shift) | value << shift
    return (held, channel[1]) if field == 0 else (channel[0], held)


def _refused(address: int) -> OutOfRange:
    return OutOfRange(f"{address:#08x} is not an address this chip answers")


class Chip:
    __slots__ = ("banks", "channels", "expansion", "hard", "model", "ready", "rom", "soft")

    def __init__(
        self, model: str, rom: bytes | bytearray | None = None, seed: int = UNSET_SEED
    ) -> None:
        scrambled = random.Random(seed)
        held = scrambled.randbytes(ROM_BYTES) if rom is None else bytes(rom)
        if not held:
            raise EmptyRom("a cartridge needs a ROM for the S-DD1 to sit in front of")
        self.model = model
        self.rom = held
        self.hard = scrambled.randrange(0x100)
        self.soft = scrambled.randrange(0x100)
        self.banks = tuple(scrambled.randrange(0x100) & BANK_WRITE_MASK for _ in RESET_BANKS)
        self.channels = tuple(
            (scrambled.randrange(1 << 24), scrambled.randrange(1 << 16)) for _ in range(CHANNELS)
        )
        self.ready = bool(scrambled.getrandbits(1))
        self.expansion = Expansion(self._mapped, scrambled.randrange(1 << 24))

    def reset(self) -> "Chip":
        self.hard = 0
        self.soft = 0
        self.banks = RESET_BANKS
        self.channels = tuple((0, 0) for _ in range(CHANNELS))
        self.ready = False
        return self

    def decompress(self, rom: bytes | bytearray, offset: int, length: int) -> Any:
        return decompress(rom, offset, length)

    def _byte(self, index: int) -> int:
        return self.rom[index % len(self.rom)]

    def _mapped(self, address: int) -> int:
        bank = self.banks[(address >> MEGABYTE_SHIFT) & 3] & BANK_NUMBER_MASK
        return self._byte(bank << MEGABYTE_SHIFT | (address & MEGABYTE_MASK))

    def _program(self, address: int) -> int:
        folds = self.banks[3 if address & 0x800000 else 1] & LOROM_REMAP_BIT
        if folds:
            address &= ~UPPER_HALF
        page = (address >> 16) & 0x3F
        return self._byte(page << LOROM_PAGE_SHIFT | (address & LOROM_PAGE_MASK))

    def _register(self, address: int) -> int:
        register = REGISTER_WINDOW | (address & 0xF)
        if register == HARD_ENABLE:
            return self.hard
        if register == SOFT_ENABLE:
            return self.soft
        if FIRST_BANK <= register < FIRST_BANK + len(RESET_BANKS):
            return self.banks[register - FIRST_BANK]
        return self._byte(register)

    def _streamed(self, channel: int) -> int:
        address, size = self.channels[channel]
        if not self.ready:
            self.expansion = Expansion(self._mapped, address)
            self.ready = True
        value = self.expansion.byte()
        size = (size - 1) & SIZE_MASK
        self.channels = (*self.channels[:channel], (address, size), *self.channels[channel + 1 :])
        if size == 0:
            self.ready = False
            self.soft &= ~(1 << channel)
        return value

    def _window(self, address: int) -> int:
        armed = self.hard & self.soft
        for channel in range(CHANNELS):
            if armed >> channel & 1 and address == self.channels[channel][0]:
                return self._streamed(channel)
        return self._mapped(address)

    def read(self, address: int) -> int:
        address &= ADDRESS_MASK
        bank, offset = address >> 16, address & 0xFFFF
        if bank >= MMC_FIRST_BANK:
            return self._window(address)
        if bank & ~MIRROR_BANK >= LOW_BANK_LIMIT:
            raise _refused(address)
        if offset >= PROGRAM_WINDOW:
            return self._program(address)
        if offset & 0xFFF0 == REGISTER_WINDOW:
            return self._register(address)
        raise _refused(address)

    def _store(self, offset: int, value: int) -> None:
        register = REGISTER_WINDOW | (offset & 0xF)
        if register == HARD_ENABLE:
            self.hard = value
        elif register == SOFT_ENABLE:
            self.soft = value
        elif FIRST_BANK <= register < FIRST_BANK + len(RESET_BANKS):
            at = register - FIRST_BANK
            self.banks = (*self.banks[:at], value & BANK_WRITE_MASK, *self.banks[at + 1 :])

    def _snoop(self, offset: int, value: int) -> None:
        register = offset & 0xF
        if register not in SNOOPED:
            return
        at = (offset >> 4) & 7
        changed = _snooped(self.channels[at], register, value)
        self.channels = (*self.channels[:at], changed, *self.channels[at + 1 :])

    def write(self, address: int, value: int) -> None:
        address &= ADDRESS_MASK
        bank, offset = address >> 16, address & 0xFFFF
        if bank >= MMC_FIRST_BANK:
            return
        if bank & ~MIRROR_BANK >= LOW_BANK_LIMIT:
            raise _refused(address)
        if offset >= PROGRAM_WINDOW:
            return
        if offset & 0xFFF0 == REGISTER_WINDOW:
            self._store(offset, value & 0xFF)
        elif DMA_WINDOW <= offset <= DMA_WINDOW_END:
            self._snoop(offset, value & 0xFF)
        else:
            raise _refused(address)

    @override
    def __repr__(self) -> str:
        banks = " ".join(f"{bank:02x}" for bank in self.banks)
        return f"<Chip {self.model} enable {self.hard:02x}/{self.soft:02x} banks {banks}>"
