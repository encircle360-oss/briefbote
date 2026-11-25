"""Where a page of a printout is painted, read from the page rendered to a greyscale image (PGM, as `pdftoppm -gray`
writes it), for what has no words to measure, such as a logo: an image or an SVG that a generator embeds as an image
or as paths. The module imports no Frappe."""

import re
from dataclasses import dataclass

# A pixel lighter than this is paper; anti-aliasing leaves the edge of a shape a little lighter than the shape.
PAPER = 235
INCH_MM = 25.4


@dataclass(frozen=True, slots=True)
class Raster:
	width: int
	height: int
	dpi: float
	pixels: bytes


@dataclass(frozen=True, slots=True)
class Area:
	"""A rectangle on the page in millimetres from its top left corner."""

	left: float
	top: float
	right: float
	bottom: float

	@property
	def width(self) -> float:
		return self.right - self.left

	@property
	def height(self) -> float:
		return self.bottom - self.top


def read_pgm(data: bytes, dpi: float) -> Raster:
	"""A binary PGM with 8 bits a pixel."""
	head = re.match(rb"P5(?:\s+|#[^\n]*\n)+(\d+)\s+(\d+)\s+(\d+)\s", data)
	if not head or int(head.group(3)) > 255:
		raise ValueError("not a binary greyscale PGM with 8 bits a pixel")
	width, height = int(head.group(1)), int(head.group(2))
	pixels = data[head.end() : head.end() + width * height]
	if len(pixels) < width * height:
		raise ValueError("the PGM ends before its last pixel")
	return Raster(width, height, dpi, pixels)


def painted(raster: Raster, within: Area) -> Area | None:
	"""The smallest rectangle that holds every painted pixel within the area, or None where it is blank."""
	scale = raster.dpi / INCH_MM
	left, top = max(int(within.left * scale), 0), max(int(within.top * scale), 0)
	right, bottom = (
		min(int(within.right * scale), raster.width),
		min(int(within.bottom * scale), raster.height),
	)
	columns, rows = [], []
	for y in range(top, bottom):
		row = raster.pixels[y * raster.width + left : y * raster.width + right]
		dark = [x for x, value in enumerate(row) if value < PAPER]
		if dark:
			rows.append(y)
			columns += (dark[0] + left, dark[-1] + left)
	if not rows:
		return None
	return Area(min(columns) / scale, rows[0] / scale, (max(columns) + 1) / scale, (rows[-1] + 1) / scale)
