"""Synthetic colour/geometry checks for the independent Z7 raw merge (MIT)."""
import sys
import unittest
import tempfile
import argparse
import contextlib
import io
import json
from unittest.mock import patch
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from merge_z7_pixel_shift import interlace, illumination_levels, illumination_gains, illumination_field, expand_field, translate_plane
from merge_z7_pixel_shift_highres import interlace_scaled, write_rows


PATTERN = np.array([[0, 1], [3, 2]])
CORNERS = [(0, 0), (-1, 0), (-1, 1), (0, 1)]


def scene(x, y, c):
    return .18 + .05 * c + .035 * np.sin(x * .2) + .03 * np.cos(y * .17)


def mosaic(shift, exposure=(1., 1., 1.), size=320):
    y, x = np.mgrid[:size, :size]
    colour = PATTERN[y % 2, x % 2].copy()
    colour[colour == 3] = 1
    return (scene(x - shift[0], y - shift[1], colour) * np.array(exposure)[colour]).astype(np.float32)


class PixelShiftMergeTests(unittest.TestCase):
    def merge(self, shifts, match=True, fractional=True):
        acc = np.zeros((304, 304, 3), np.float32)
        ref = illumination_levels(mosaic(shifts[0]), PATTERN, block=8)
        for k, shift in enumerate(shifts):
            raw = mosaic(shift, [(1, 1, 1), (.90, .91, .89), (.88, .90, .87), (.97, .98, .96)][k])
            gains = illumination_gains(ref, illumination_levels(raw, PATTERN, block=8)) if match else [1., 1., 1.]
            interlace(acc, raw, PATTERN, shift if fractional else CORNERS[k], CORNERS[k], 8, gains)
        acc[..., 1] *= .5
        return acc

    def test_integer_corners_recover_true_rgb_without_colour_mixing(self):
        acc = np.zeros((304, 304, 3), np.float32)
        for shift in CORNERS:
            interlace(acc, mosaic(shift), PATTERN, shift, shift, 8, [1., 1., 1.])
        acc[..., 1] *= .5
        y, x = np.mgrid[8:312, 8:312]
        expected = np.stack([scene(x, y, c) for c in range(3)], axis=-1)
        np.testing.assert_allclose(acc, expected, atol=5e-8)

    def test_fractional_alignment_reduces_geometry_error(self):
        shifts = [(0, 0), (-1.12, -.02), (-1.12, .90), (0, .86)]
        results = []
        y, x = np.mgrid[8:312, 8:312]
        expected = np.stack([scene(x, y, c) for c in range(3)], axis=-1)
        for fractional in (False, True):
            acc = np.zeros((304, 304, 3), np.float32)
            for k, shift in enumerate(shifts):
                interlace(acc, mosaic(shift), PATTERN, shift if fractional else CORNERS[k], CORNERS[k], 8, [1., 1., 1.])
            acc[..., 1] *= .5
            results.append(float(np.mean((acc - expected) ** 2)))
        self.assertLess(results[1], results[0] / 10)

    def test_illumination_matching_removes_alternating_phase_brightness(self):
        before, after = self.merge(CORNERS, match=False), self.merge(CORNERS)
        y, x = np.mgrid[8:312, 8:312]
        expected = np.stack([scene(x, y, c) for c in range(3)], axis=-1)
        self.assertLess(np.mean((after - expected) ** 2), np.mean((before - expected) ** 2) / 100)

    def test_constant_planes_stay_constant_when_shifted(self):
        plane = np.full((50, 50), .23, np.float32)
        np.testing.assert_allclose(translate_plane(plane, -.06, .07), plane, atol=1e-7)

    def test_spatial_illumination_matching_removes_bands_global_gain_cannot(self):
        y, x = np.mgrid[:640, :640]
        ref = np.full((640, 640), .2, np.float32)
        light = 1 + .10 * np.sin(y * .006) + .05 * np.cos(x * .005)
        other = (ref * light).astype(np.float32)
        a, b = illumination_levels(ref, PATTERN), illumination_levels(other, PATTERN)
        gains = illumination_gains(a, b)
        field = illumination_field(a, b, gains)
        corrected = other[::2, ::2] * expand_field(field[0], (320, 320))
        crop = np.s_[48:-48, 48:-48]
        error = np.mean((corrected[crop] - .2) ** 2)
        global_error = np.mean((other[::2, ::2][crop] * gains[0] - .2) ** 2)
        self.assertLess(error, global_error / 20)

    def test_dark_clipped_or_extreme_exposures_are_rejected(self):
        for a, b in ((0., .2), (1., 1.), (.2, .08)):
            with self.assertRaises(ValueError):
                illumination_gains(np.full((3, 8, 8), a), np.full((3, 8, 8), b))

    def test_16_and_32_half_step_frames_recover_double_resolution_rgb(self):
        for count in (16,32):
            with self.subTest(count=count):
                acc=np.zeros((608,608,3),np.float32)
                counts=np.zeros((4,4,3),np.uint16)
                offsets=[(0,0),(-.5,0),(-.5,.5),(0,.5)]
                for k in range(count):
                    cx,cy=CORNERS[k%4];px,py=offsets[(k//4)%4]
                    shift=(cx+px,cy+py)
                    interlace_scaled(acc,counts,mosaic(shift),PATTERN,shift,
                                     tuple(int(round(v*2)) for v in shift),(8,8),[1.,1.,1.])
                self.assertTrue((counts>0).all())
                acc/=counts[np.arange(608)[:,None]%4,np.arange(608)[None,:]%4]
                y,x=np.mgrid[:608,:608]
                expected=np.stack([scene(8+x/2,8+y/2,c) for c in range(3)],axis=-1)
                np.testing.assert_allclose(acc,expected,atol=6e-8)

    def test_streaming_tiff_keeps_uint16_samples_and_dimensions(self):
        from PIL import Image
        data=np.arange(11*13*3,dtype=np.uint16).reshape(11,13,3)*101
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'out.tif'
            write_rows(path,data.shape,[data[:7],data[7:]])
            with Image.open(path) as im:
                self.assertEqual(im.size,(13,11))
                self.assertEqual(im.tag_v2[258],(16,16,16))
            decoded=np.frombuffer(path.read_bytes(),dtype='<u2',offset=140).reshape(data.shape)
            np.testing.assert_array_equal(decoded,data)

    def test_highres_pipeline_exports_a_complete_synthetic_16_shot_set(self):
        import merge_z7_pixel_shift_highres as highres
        shifts=[]
        for k in range(16):
            cx,cy=CORNERS[k%4];px,py=((0,0),(-.5,0),(-.5,.5),(0,.5))[k//4]
            shifts.append((cx+px,cy+py))
        class Raw:
            def close(self):pass
            def postprocess(self,**kw):
                y,x=np.mgrid[:320,:320]
                return np.round(np.stack([scene(x,y,c) for c in range(3)],axis=-1)*65535).astype(np.uint16)
        photos=[Path(f'frame-{k}.NEF') for k in range(16)]
        def fake_load(path):
            k=photos.index(path)
            return Raw(),mosaic(shifts[k]),dict(pattern=PATTERN,wb=np.ones(3),cam=np.eye(3),crop_margin=(8,8),crop_size=(304,304))
        with tempfile.TemporaryDirectory() as folder:
            a=argparse.Namespace(photos=photos,shifts=';'.join(f'{x},{y}' for x,y in shifts[1:]),
                                 shift_report=None,alignment='subpixel',photometric='none',output=Path(folder))
            with patch.object(highres,'load',side_effect=fake_load),contextlib.redirect_stdout(io.StringIO()):
                highres.run(a,argparse.ArgumentParser())
            report=json.loads((a.output/'merge.json').read_text())
            self.assertEqual(report['size'],[608,608])
            self.assertFalse((a.output/'accumulator.work').exists())
            from PIL import Image
            with Image.open(a.output/'merged.tif') as im:self.assertEqual(im.size,(608,608))

    def test_eight_shot_native_resolution_merge_averages_two_corner_sets(self):
        import merge_z7_pixel_shift as merger
        size=800
        class Raw:
            def close(self):pass
            def postprocess(self,**kw):
                y,x=np.mgrid[:size,:size]
                return np.round(np.stack([scene(x,y,c) for c in range(3)],axis=-1)*65535).astype(np.uint16)
        photos=[Path(f'frame-{k}.NEF') for k in range(8)]
        def fake_load(path):
            k=photos.index(path)
            return Raw(),mosaic(CORNERS[k%4],size=size),dict(pattern=PATTERN,wb=np.ones(3),cam=np.eye(3),crop_margin=(8,8),crop_size=(784,784))
        results=[]
        with tempfile.TemporaryDirectory() as folder:
            for count in (4,8):
                output=Path(folder)/str(count)
                shifts=';'.join(f'{x},{y}' for x,y in [CORNERS[k%4] for k in range(1,count)])
                with patch.object(merger,'load',side_effect=fake_load),contextlib.redirect_stdout(io.StringIO()):
                    merger.main([str(p) for p in photos[:count]]+[f'--shifts={shifts}','--output',str(output)])
                report=json.loads((output/'merge.json').read_text())
                self.assertEqual(report['size'],[784,784])
                results.append(np.frombuffer((output/'merged.tif').read_bytes(),dtype='<u2',offset=140).copy())
        np.testing.assert_allclose(results[0],results[1],atol=1)

    def test_pixel_log_decoder_rejects_wrong_layout_and_bounds(self):
        import struct
        from decode_z7_pixel_menu_log import decode
        data=bytearray(184+512*56)
        struct.pack_into('<4I',data,0,0x564d5637,4,0,1<<19)
        struct.pack_into('<I',data,48,32)
        self.assertEqual(decode(data)['frames'],32)
        self.assertIn('series_complete',decode(data)['flags'])
        for offset,value in ((4,3),(8,513),(48,33)):
            bad=bytearray(data);struct.pack_into('<I',bad,offset,value)
            with self.assertRaises(ValueError):decode(bad)


if __name__ == '__main__':
    unittest.main()
