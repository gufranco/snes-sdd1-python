import hashlib
import json
import random
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import sdd1  # noqa: E402

VECTORS = json.loads((ROOT / "conformance" / "vectors.json").read_text())
BLOB = bytes.fromhex(VECTORS["input"])
CASE = VECTORS["cases"][0]

MEGABYTE = 0x100000

RESET_BANKS = [0, 1, 2, 3]


def a_rom(size: int = 4 * MEGABYTE, seed: int = 7110) -> bytearray:
    return bytearray(random.Random(seed).randbytes(size))


def with_the_noise_at(where: int) -> bytearray:
    rom = a_rom()
    rom[where : where + len(BLOB)] = BLOB
    return rom


def a_reset_chip(rom: bytes | bytearray | None = None) -> Any:
    return sdd1.Chip("sdd1", rom if rom is not None else a_rom()).reset()


def banks_of(chip: Any) -> list[int]:
    return [chip.read(address) for address in range(0x4804, 0x4808)]


def armed(chip: Any, channel: int, address: int, size: int) -> None:
    base = 0x4300 | channel << 4
    for register, value in enumerate(
        (address & 0xFF, address >> 8 & 0xFF, address >> 16, size & 0xFF, size >> 8), start=2
    ):
        chip.write(base | register, value)
    chip.write(0x4800, 1 << channel)
    chip.write(0x4801, 1 << channel)


class PowerOnTest(unittest.TestCase):
    def test_the_registers_come_up_holding_what_the_seed_left_there(self) -> None:
        # Arrange
        rom = a_rom()

        # Act
        built = [banks_of(sdd1.Chip("sdd1", rom, seed=seed)) for seed in (1, 2)]

        # Assert
        self.assertNotEqual(built[0], built[1])

    def test_and_the_same_seed_brings_them_up_the_same_way(self) -> None:
        # Arrange
        rom = a_rom()

        # Act
        built = [banks_of(sdd1.Chip("sdd1", rom, seed=3)) for _ in range(2)]

        # Assert
        self.assertEqual(built[0], built[1])

    def test_construction_does_not_reset_the_part(self) -> None:
        # Arrange
        rom = a_rom()

        # Act
        built = banks_of(sdd1.Chip("sdd1", rom))

        # Assert
        self.assertNotEqual(built, RESET_BANKS)

    def test_a_reset_maps_the_four_windows_onto_the_first_four_megabytes(self) -> None:
        # Arrange
        chip = sdd1.Chip("sdd1", a_rom())

        # Act
        chip.reset()

        # Assert
        self.assertEqual(banks_of(chip), RESET_BANKS)

    def test_and_disables_decompression_on_every_channel(self) -> None:
        # Arrange
        chip = sdd1.Chip("sdd1", a_rom())

        # Act
        chip.reset()

        # Assert
        self.assertEqual((chip.read(0x4800), chip.read(0x4801)), (0, 0))

    def test_a_part_built_without_a_rom_builds_a_scrambled_one(self) -> None:
        # Arrange
        size = 4 * MEGABYTE

        # Act
        chip = sdd1.Chip("sdd1")

        # Assert
        self.assertEqual(len(chip.rom), size)
        self.assertNotEqual(chip.rom[:16], bytes(16))

    def test_an_empty_rom_is_refused(self) -> None:
        # Arrange
        rom = b""

        # Act
        attempt = lambda: sdd1.Chip("sdd1", rom)  # noqa: E731

        # Assert
        self.assertRaises(sdd1.EmptyRom, attempt)


class RegisterTest(unittest.TestCase):
    def test_a_bank_register_keeps_bit_seven_and_the_low_four_bits(self) -> None:
        # Arrange
        chip = a_reset_chip()

        # Act
        chip.write(0x4804, 0xFF)

        # Assert
        self.assertEqual(chip.read(0x4804), 0x8F)

    def test_the_enables_keep_every_bit(self) -> None:
        # Arrange
        chip = a_reset_chip()

        # Act
        chip.write(0x4800, 0xA5)
        chip.write(0x4801, 0x5A)

        # Assert
        self.assertEqual((chip.read(0x4800), chip.read(0x4801)), (0xA5, 0x5A))

    def test_the_registers_answer_in_both_halves_of_the_bank_range(self) -> None:
        # Arrange
        chip = a_reset_chip()

        # Act
        chip.write(0xBF4805, 0x07)

        # Assert
        self.assertEqual(chip.read(0x004805), 0x07)

    def test_an_address_without_a_register_reads_the_rom_at_that_address(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)

        # Act
        found = [chip.read(address) for address in (0x4802, 0x4803, 0x4808, 0x480F)]

        # Assert
        self.assertEqual(found, [rom[0x4802], rom[0x4803], rom[0x4808], rom[0x480F]])

    def test_a_write_to_an_address_without_a_register_changes_nothing(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)

        # Act
        chip.write(0x4802, rom[0x4802] ^ 0xFF)

        # Assert
        self.assertEqual(chip.read(0x4802), rom[0x4802])


class WindowTest(unittest.TestCase):
    def test_each_window_reads_the_megabyte_its_register_names(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)

        # Act
        found = [chip.read(0xC00000 + window * 0x100000 + 0x1234) for window in range(4)]

        # Assert
        self.assertEqual(found, [rom[window * MEGABYTE + 0x1234] for window in range(4)])

    def test_a_bank_register_moves_its_window(self) -> None:
        # Arrange
        rom = a_rom(8 * MEGABYTE)
        chip = a_reset_chip(rom)

        # Act
        chip.write(0x4807, 0x05)

        # Assert
        self.assertEqual(chip.read(0xF0ABCD), rom[5 * MEGABYTE + 0xABCD])

    def test_a_rom_smaller_than_the_window_repeats(self) -> None:
        # Arrange
        rom = a_rom(2 * MEGABYTE)
        chip = a_reset_chip(rom)

        # Act
        found = chip.read(0xE00010)

        # Assert
        self.assertEqual(found, rom[0x10])

    def test_a_write_to_the_window_changes_nothing(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)

        # Act
        chip.write(0xC00000, rom[0] ^ 0xFF)

        # Assert
        self.assertEqual(chip.read(0xC00000), rom[0])


class ProgramMapTest(unittest.TestCase):
    def test_the_program_area_is_thirty_two_kilobytes_a_bank(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)

        # Act
        found = [chip.read(address) for address in (0x008000, 0x018000, 0x3FFFFF, 0x80FFFF)]

        # Assert
        self.assertEqual(found, [rom[0], rom[0x8000], rom[0x1FFFFF], rom[0x7FFF]])

    def test_bit_seven_of_the_second_bank_register_folds_banks_20_to_3f_down(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)
        before = chip.read(0x208000)

        # Act
        chip.write(0x4805, 0x81)

        # Assert
        self.assertEqual((before, chip.read(0x208000)), (rom[0x100000], rom[0]))

    def test_and_bit_seven_of_the_fourth_folds_banks_a0_to_bf(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)
        chip.write(0x4805, 0x81)
        upper_before = chip.read(0xA08000)

        # Act
        chip.write(0x4807, 0x83)

        # Assert
        self.assertEqual((upper_before, chip.read(0xA08000)), (rom[0x100000], rom[0]))

    def test_a_write_to_the_program_area_changes_nothing(self) -> None:
        # Arrange
        rom = a_rom()
        chip = a_reset_chip(rom)

        # Act
        chip.write(0x008000, rom[0] ^ 0xFF)

        # Assert
        self.assertEqual(chip.read(0x008000), rom[0])


class DecompressionTest(unittest.TestCase):
    def test_a_channel_reading_its_own_source_gets_the_decoded_stream(self) -> None:
        # Arrange
        chip = a_reset_chip(with_the_noise_at(2 * MEGABYTE))
        source = 0xE00000 + CASE["offset"]
        armed(chip, 3, source, CASE["length"])

        # Act
        found = bytes(chip.read(source) for _ in range(CASE["length"]))

        # Assert
        self.assertEqual(hashlib.sha256(found).hexdigest(), CASE["output_sha256"])

    def test_the_stream_is_read_through_the_bank_registers(self) -> None:
        # Arrange
        chip = a_reset_chip(with_the_noise_at(3 * MEGABYTE))
        chip.write(0x4804, 0x03)
        source = 0xC00000 + CASE["offset"]
        armed(chip, 0, source, CASE["length"])

        # Act
        found = bytes(chip.read(source) for _ in range(CASE["length"]))

        # Assert
        self.assertEqual(hashlib.sha256(found).hexdigest(), CASE["output_sha256"])

    def test_the_last_byte_of_a_transfer_disarms_that_channel(self) -> None:
        # Arrange
        chip = a_reset_chip(with_the_noise_at(0))
        armed(chip, 2, 0xC00000 + CASE["offset"], 4)

        # Act
        for _ in range(4):
            chip.read(0xC00000 + CASE["offset"])

        # Assert
        self.assertEqual((chip.read(0x4800), chip.read(0x4801)), (0x04, 0x00))

    def test_after_which_the_source_reads_as_rom_again(self) -> None:
        # Arrange
        rom = with_the_noise_at(0)
        chip = a_reset_chip(rom)
        armed(chip, 2, 0xC00000 + CASE["offset"], 4)
        for _ in range(4):
            chip.read(0xC00000 + CASE["offset"])

        # Act
        found = chip.read(0xC00000 + CASE["offset"])

        # Assert
        self.assertEqual(found, rom[CASE["offset"]])

    def test_a_size_of_zero_transfers_one_whole_block(self) -> None:
        # Arrange
        chip = a_reset_chip(with_the_noise_at(0))
        armed(chip, 1, 0xC00000, 0)
        for _ in range(0xFFFF):
            chip.read(0xC00000)
        still = chip.read(0x4801)

        # Act
        chip.read(0xC00000)

        # Assert
        self.assertEqual((still, chip.read(0x4801)), (0x02, 0x00))

    def test_a_channel_set_only_in_the_second_enable_does_not_decompress(self) -> None:
        # Arrange
        rom = with_the_noise_at(0)
        chip = a_reset_chip(rom)
        armed(chip, 0, 0xC00000 + CASE["offset"], 8)

        # Act
        chip.write(0x4800, 0x00)

        # Assert
        self.assertEqual(chip.read(0xC00000 + CASE["offset"]), rom[CASE["offset"]])

    def test_another_address_in_the_window_reads_rom_while_a_channel_is_armed(self) -> None:
        # Arrange
        rom = with_the_noise_at(0)
        chip = a_reset_chip(rom)
        armed(chip, 0, 0xC00000 + CASE["offset"], 8)

        # Act
        found = chip.read(0xC00001 + CASE["offset"])

        # Assert
        self.assertEqual(found, rom[CASE["offset"] + 1])

    def test_a_snooped_register_outside_address_and_size_changes_nothing(self) -> None:
        # Arrange
        rom = with_the_noise_at(0)
        chip = a_reset_chip(rom)
        armed(chip, 0, 0xC00000 + CASE["offset"], CASE["length"])
        chip.write(0x4300, 0x09)
        chip.write(0x4307, 0x01)

        # Act
        found = bytes(chip.read(0xC00000 + CASE["offset"]) for _ in range(CASE["length"]))

        # Assert
        self.assertEqual(hashlib.sha256(found).hexdigest(), CASE["output_sha256"])


class DecodeTest(unittest.TestCase):
    def test_a_part_also_decodes_a_stream_held_in_a_buffer(self) -> None:
        # Arrange
        chip = sdd1.Chip("sdd1")

        # Act
        found = chip.decompress(BLOB, CASE["offset"], CASE["length"])

        # Assert
        self.assertEqual(hashlib.sha256(found.data).hexdigest(), CASE["output_sha256"])


class OutOfRangeTest(unittest.TestCase):
    def test_an_address_the_chip_does_not_decode_is_refused_on_a_read(self) -> None:
        # Arrange
        chip = a_reset_chip()

        # Act
        refused = []
        for address in (0x002000, 0x004300, 0x7E0000, 0x400000, 0x404800):
            with self.assertRaises(sdd1.OutOfRange) as raised:
                chip.read(address)
            refused.append(str(raised.exception))

        # Assert
        self.assertEqual(refused[0], "0x002000 is not an address this chip answers")
        self.assertEqual(len(refused), 5)

    def test_and_on_a_write(self) -> None:
        # Arrange
        chip = a_reset_chip()

        # Act
        refused = 0
        for address in (0x002000, 0x7E0000, 0x404800):
            with self.assertRaises(sdd1.OutOfRange):
                chip.write(address, 0)
            refused += 1

        # Assert
        self.assertEqual(refused, 3)


class ReprTest(unittest.TestCase):
    def test_a_part_shows_its_enables_and_its_banks(self) -> None:
        # Arrange
        chip = a_reset_chip()

        # Act
        shown = repr(chip)

        # Assert
        self.assertEqual(shown, "<Chip sdd1 enable 00/00 banks 00 01 02 03>")


if __name__ == "__main__":
    unittest.main()
