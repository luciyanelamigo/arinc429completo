import unittest

from arinc429 import build_word, encode_data, word_hex


class Arinc429WordTests(unittest.TestCase):
    def test_builds_32_bit_word_with_odd_parity(self):
        word = build_word("204", 2, 12345, 1)
        self.assertLessEqual(word, 0xFFFFFFFF)
        self.assertEqual(word.bit_count() % 2, 1)

    def test_label_is_bit_reversed_into_low_byte(self):
        # Octal 001 is logical label value 1, reversed as 10000000b.
        self.assertEqual(build_word("001", 0, 0, 0) & 0xFF, 0x80)

    def test_encodes_signed_bnr_twos_complement_field(self):
        self.assertEqual(encode_data(-3, "BNR", 1), (1 << 19) - 3)

    def test_requires_resolution_multiple(self):
        with self.assertRaises(ValueError):
            encode_data(1.1, "BNR", 0.5)

    def test_hex_has_fixed_width(self):
        self.assertEqual(word_hex(7), "0x00000007")


if __name__ == "__main__":
    unittest.main()
