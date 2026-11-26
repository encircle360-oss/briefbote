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
	head = re.match(rb"P5(?:\s|#[^\n]*\n)+(\d+)\s(?:\s|#[^\n]*\n)*(\d+)\s(?:\s|#[^\n]*\n)*(\d+)\s", data)
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


def share(raster: Raster, within: Area, low: int, high: int) -> float:
	"""The share of the pixels within the area whose grey lies between low and high, such as a light mark that is
	neither paper nor text."""
	scale = raster.dpi / INCH_MM
	left, top = max(int(within.left * scale), 0), max(int(within.top * scale), 0)
	right, bottom = (
		min(int(within.right * scale), raster.width),
		min(int(within.bottom * scale), raster.height),
	)
	pixels = [
		value
		for y in range(top, bottom)
		for value in raster.pixels[y * raster.width + left : y * raster.width + right]
	]
	return sum(low <= value <= high for value in pixels) / len(pixels) if pixels else 0


def rule(raster: Raster, within: Area, share: float = 0.8) -> float | None:
	"""The top of the first row within the area that is painted across most of its width, such as the rule above the
	foot, in millimetres from the top of the page; None where there is none."""
	scale = raster.dpi / INCH_MM
	left, top = max(int(within.left * scale), 0), max(int(within.top * scale), 0)
	right, bottom = (
		min(int(within.right * scale), raster.width),
		min(int(within.bottom * scale), raster.height),
	)
	for y in range(top, bottom):
		row = raster.pixels[y * raster.width + left : y * raster.width + right]
		if row and sum(value < PAPER for value in row) >= share * len(row):
			return y / scale
	return None


def lowest(raster: Raster, within: Area) -> float | None:
	"""The bottom of the lowest painted row within the area, in millimetres from the top of the page."""
	found = painted(raster, within)
	return found.bottom if found else None


def bands(raster: Raster, within: Area) -> list[tuple[float, float]]:
	"""The runs of painted rows within the area, top and bottom in millimetres from the top of the page: the lines of
	text, rules and frames that stand one above the other, with blank rows between them."""
	scale = raster.dpi / INCH_MM
	left, top = max(int(within.left * scale), 0), max(int(within.top * scale), 0)
	right, bottom = (
		min(int(within.right * scale), raster.width),
		min(int(within.bottom * scale), raster.height),
	)
	found: list[tuple[int, int]] = []
	for y in range(top, bottom):
		row = raster.pixels[y * raster.width + left : y * raster.width + right]
		if any(value < PAPER for value in row):
			if found and found[-1][1] == y:
				found[-1] = (found[-1][0], y + 1)
			else:
				found.append((y, y + 1))
	return [(start / scale, end / scale) for start, end in found]
