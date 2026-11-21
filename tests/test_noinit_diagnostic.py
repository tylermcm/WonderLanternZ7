from pathlib import Path
import hashlib
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_z7_module import pack_module,seal,HEADER
from build_z7_noinit_diagnostic import disable_entry,RETURN_ZERO


class NoInitTests(unittest.TestCase):
    def packet(self,entry=0,relocs=(64,)):
        image=bytearray(bytes.fromhex('00bf')*64)
        struct.pack_into('<I',image,64,68)
        return pack_module(image,64,entry,relocs)

    def transform(self,packet):
        return disable_entry(packet,hashlib.sha256(packet).hexdigest())

    def test_only_entry_and_crc_change_and_layout_is_identical(self):
        source=self.packet(); result,meta=self.transform(source)
        self.assertEqual(len(source),len(result))
        self.assertEqual(result[HEADER:HEADER+4],RETURN_ZERO)
        allowed=set(range(32,36))|set(range(HEADER,HEADER+4))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,result))))
        self.assertEqual(meta['relocations'],[64])
        self.assertEqual(meta['bss_bytes'],64)
        self.assertEqual(seal(result),result)

    def test_wrong_fingerprint_and_crc_are_rejected(self):
        source=self.packet()
        with self.assertRaises(ValueError): disable_entry(source,'0'*64)
        changed=bytearray(source);changed[-1]^=1
        with self.assertRaises(ValueError): self.transform(changed)

    def test_entry_overlapping_relocation_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'overlaps'): self.transform(self.packet(entry=64))

    def test_entry_near_end_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'boundary'): self.transform(self.packet(entry=126))

    def test_other_target_and_reserved_header_are_rejected(self):
        for offset in (8,36):
            source=bytearray(self.packet());struct.pack_into('<I',source,offset,1)
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.transform(seal(source))


if __name__ == '__main__':unittest.main()
