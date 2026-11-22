import binascii
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from grid_restore_record import encode,decode


class GridRestoreRecordTests(unittest.TestCase):
    def test_all_layouts_roundtrip(self):
        for choice in range(1,6):self.assertEqual(decode(encode(choice)),choice)

    def test_every_single_bit_error_is_rejected(self):
        original=encode(5)
        for bit in range(80*8):
            data=bytearray(original);data[bit//8]^=1<<(bit%8)
            with self.assertRaises(ValueError):decode(data)

    def test_semantically_invalid_records_fail_even_with_valid_crc(self):
        for offset,value in ((0,0),(4,2),(8,79),(16,0),(16,6),(20,1)):
            data=bytearray(encode(5));struct.pack_into('<I',data,offset,value);data[12:16]=bytes(4);struct.pack_into('<I',data,12,binascii.crc32(data))
            with self.assertRaises(ValueError):decode(data)

    def test_length_and_encoder_bounds(self):
        for data in (b'',encode(5)[:-1],encode(5)+b'\0'):
            with self.assertRaises(ValueError):decode(data)
        for choice in (0,6,-1,1.5,None):
            with self.assertRaises(ValueError):encode(choice)


if __name__=='__main__':unittest.main()
