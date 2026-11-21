from pathlib import Path
import hashlib,struct,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_z7_module import pack_module,HEADER,seal
from build_z7_noinit_diagnostic import RETURN_ZERO
from build_z7_no_settings_io_diagnostic import suppress_settings_io


class NoSettingsIOTests(unittest.TestCase):
    def setUp(self):
        image=bytearray(bytes.fromhex('00bf')*64);struct.pack_into('<I',image,64,68)
        self.packet=pack_module(image,64,0,[64])
        self.digest=hashlib.sha256(self.packet).hexdigest()
        self.symbols={'persistence_prepare':9,'persistence_worker':17}

    def transform(self,symbols=None):
        return suppress_settings_io(self.packet,self.digest,self.symbols if symbols is None else symbols)

    def test_only_two_functions_and_crc_change_entry_stays_intact(self):
        result,layout,patches=self.transform()
        self.assertEqual(len(result),len(self.packet));self.assertEqual(result[HEADER:HEADER+4],self.packet[HEADER:HEADER+4])
        allowed=set(range(32,36))
        for offset in patches.values():
            self.assertEqual(result[HEADER+offset:HEADER+offset+4],RETURN_ZERO)
            allowed.update(range(HEADER+offset,HEADER+offset+4))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(self.packet,result))))
        self.assertEqual(layout['relocations'],[64]);self.assertEqual(seal(result),result)

    def test_missing_or_non_thumb_symbol_is_rejected(self):
        for symbols in ({},{**self.symbols,'persistence_prepare':8}):
            with self.assertRaises(ValueError):self.transform(symbols)

    def test_entry_relocation_and_function_overlaps_are_rejected(self):
        for value in (1,65,17,127):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.transform({**self.symbols,'persistence_prepare':value})

    def test_wrong_source_fingerprint_is_rejected(self):
        with self.assertRaises(ValueError):suppress_settings_io(self.packet,'0'*64,self.symbols)


if __name__=='__main__':unittest.main()
