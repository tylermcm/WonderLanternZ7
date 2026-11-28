"""Exposure-group identity and failure interpretation, independent fixtures (MIT)."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from decode_z7_pixel_menu_log import decode


def log(frames=288,groups=9,shots=32,complete=9):
    data=bytearray(329*4+4608*56)
    struct.pack_into('<4I',data,0,0x564d5637,5,1,1<<19)
    struct.pack_into('<I',data,12*4,frames)
    struct.pack_into('<'+'I'*frames,data,14*4,*range(10001,10001+frames))
    struct.pack_into('<3I',data,302*4,groups,shots,complete)
    struct.pack_into('<9i',data,305*4,0,-6,6,-12,12,-18,18,-24,24)
    struct.pack_into('<6i',data,314*4,3,0,120,48,0,-24)
    struct.pack_into('<IBBH',data,329*4,123,7,frames&255,0)
    struct.pack_into('<H',data,329*4+50,frames)
    return data


class PixelExposureLogTests(unittest.TestCase):
    def test_all_288_keys_split_into_nine_complete_exposures(self):
        result=decode(log())
        self.assertEqual(len(result['groups']),9)
        self.assertEqual(result['groups'][-1]['file_keys'],list(range(10257,10289)))
        self.assertTrue(all(g['complete'] for g in result['groups']))
        self.assertEqual(result['groups'][-1]['ev_sixths'],24)
        self.assertEqual(result['entries'][0]['poll'],288)
        self.assertEqual(result['exposure']['saved'][5],-24)

    def test_partial_exposure_is_retained_and_not_marked_complete(self):
        result=decode(log(40,2,32,1))
        self.assertEqual(len(result['groups'][1]['file_keys']),8)
        self.assertFalse(result['groups'][1]['complete'])

    def test_impossible_completion_and_duplicate_keys_are_rejected(self):
        with self.assertRaises(ValueError):decode(log(40,2,32,2))
        data=log();struct.pack_into('<I',data,15*4,10001)
        with self.assertRaises(ValueError):decode(data)

    def test_pending_restore_and_failure_are_exposed(self):
        data=log();struct.pack_into('<3I',data,326*4,32,2,1)
        result=decode(data)['exposure']
        self.assertEqual((result['restore_pending'],result['job_error'],result['setup_error']),(32,2,1))


if __name__=='__main__':unittest.main()
