import importlib.util
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

SCRIPTS = pathlib.Path(__file__).parents[1] / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('fetch_app_icons', SCRIPTS / 'fetch_app_icons.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IconTransparencyTests(unittest.TestCase):
    def test_rgba_and_rgb_transparency_survive_resizing(self):
        for mode in ('RGBA', 'RGB', 'P'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                if mode == 'P':
                    icon = Image.new('P', (16, 16), 0)
                    icon.putpalette([255, 255, 255, 255, 0, 0] + [0] * 762)
                    icon.info['transparency'] = 0
                    icon.paste(1, (4, 4, 12, 12))
                else:
                    icon = Image.new(mode, (16, 16), (255, 255, 255, 0) if mode == 'RGBA' else (255, 255, 255))
                    if mode == 'RGB':
                        icon.info['transparency'] = (255, 255, 255)
                    icon.paste((255, 0, 0, 255) if mode == 'RGBA' else (255, 0, 0), (4, 4, 12, 12))
                with patch.object(MODULE, 'LOGOS_DIR', directory):
                    path = MODULE.save_icon(icon, 'fixture')
                with Image.open(path) as saved:
                    self.assertEqual(saved.size, (512, 512))
                    self.assertEqual(saved.mode, 'RGBA')
                    self.assertEqual(saved.getpixel((0, 0))[3], 0)
                    self.assertEqual(saved.getpixel((256, 256))[3], 255)

    def test_intentional_opaque_background_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(MODULE, 'LOGOS_DIR', directory):
            path = MODULE.save_icon(Image.new('RGB', (16, 16), 'white'), 'opaque')
            with Image.open(path) as saved:
                self.assertEqual(saved.convert('RGBA').getpixel((0, 0)), (255, 255, 255, 255))
