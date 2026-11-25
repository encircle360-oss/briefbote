from unittest import TestCase

from briefbote.proof import raster
from briefbote.proof.raster import Area

# 25.4 dots per inch: one pixel is one millimetre.
DPI = 25.4


def pgm(width: int, height: int, dark: set[tuple[int, int]], comment: bool = False) -> bytes:
	pixels = bytes(0 if (x, y) in dark else 255 for y in range(height) for x in range(width))
	head = b"P5\n" + (b"# made by a test\n" if comment else b"") + f"{width} {height}\n255\n".encode()
	return head + pixels


class RasterTest(TestCase):
	def test_the_painted_rectangle_of_an_area(self):
		image = raster.read_pgm(pgm(20, 10, {(3, 2), (7, 5), (15, 1)}, comment=True), DPI)
		self.assertEqual(raster.painted(image, Area(0, 0, 10, 10)), Area(3, 2, 8, 6))
		self.assertEqual(raster.painted(image, Area(0, 0, 20, 10)), Area(3, 1, 16, 6))

	def test_a_blank_area_has_none(self):
		image = raster.read_pgm(pgm(20, 10, {(15, 1)}), DPI)
		self.assertIsNone(raster.painted(image, Area(0, 0, 10, 10)))

	def test_an_area_beyond_the_page_ends_at_its_edge(self):
		image = raster.read_pgm(pgm(4, 4, {(3, 3)}), DPI)
		self.assertEqual(raster.painted(image, Area(-5, -5, 50, 50)), Area(3, 3, 4, 4))

	def test_an_area_knows_its_size(self):
		self.assertEqual((Area(1, 2, 4, 8).width, Area(1, 2, 4, 8).height), (3, 6))

	def test_an_empty_or_cut_off_image_is_an_error_not_a_loop(self):
		for data in (b"", b"P5", b"P5\n10 10\n255\n" + b"\xff" * 5):
			with self.subTest(data=data[:12]), self.assertRaises(ValueError):
				raster.read_pgm(data, DPI)

	def test_only_a_binary_greyscale_image_reads(self):
		with self.assertRaises(ValueError):
			raster.read_pgm(b"P6\n1 1\n255\n\x00\x00\x00", DPI)
		with self.assertRaises(ValueError):
			raster.read_pgm(b"P5\n1 1\n65535\n\x00\x00", DPI)
