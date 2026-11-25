"""The logo of the letterhead: its proportions, read from the file, and the box it prints in.

A logo prints at the height the settings give it and the width its proportions ask for, never wider than the
letterhead allows. The print formats give the image both measures: an SVG without width and height has no size of its
own, and in the letterhead, a box as wide as its content, both PDF generators would print it with none. An SVG loses
what stands before its root element, the XML declaration, comments and a DOCTYPE, whose DTD a generator could try to
load, and gains width and height from its viewBox.
"""

import re
import struct
from decimal import Decimal, InvalidOperation

# The widest a logo prints, in millimetres: the width of the information block (briefbote/layout/din5008.py), with
# whose right edge a logo on the right ends.
MAX_WIDTH = Decimal(75)
PNG = b"\x89PNG\r\n\x1a\n"
JPEG = b"\xff\xd8"
# The markers of a JPEG frame that carry its size: SOF0 to SOF15 without DHT, JPG and DAC.
FRAMES = set(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}
SVG_ROOT = re.compile(rb"<svg\b[^>]*>", re.IGNORECASE)
LENGTH = re.compile(r"\s*([0-9]*\.?[0-9]+)\s*(px|mm|cm|in|pt|pc)?\s*$", re.IGNORECASE)
Size = tuple[Decimal, Decimal]


def _attribute(tag: bytes, name: str) -> str | None:
	match = re.search(rb"\s" + name.encode() + rb"\s*=\s*(['\"])(.*?)\1", tag, re.IGNORECASE | re.DOTALL)
	return match.group(2).decode("utf-8", "replace") if match else None


def _length(value: str | None) -> Decimal | None:
	match = LENGTH.match(value or "")
	if not match:
		return None
	try:
		return Decimal(match.group(1))
	except InvalidOperation:  # pragma: no cover - the expression admits only numbers
		return None


def _view_box(tag: bytes) -> Size | None:
	parts = (_attribute(tag, "viewBox") or "").replace(",", " ").split()
	if len(parts) != 4:
		return None
	try:
		width, height = Decimal(parts[2]), Decimal(parts[3])
	except InvalidOperation:
		return None
	return (width, height) if width > 0 and height > 0 else None


def _svg(content: bytes) -> Size | None:
	match = SVG_ROOT.search(content)
	if not match:
		return None
	tag = match.group(0)
	width, height = _length(_attribute(tag, "width")), _length(_attribute(tag, "height"))
	if width and height:
		return width, height
	return _view_box(tag)


def _jpeg(content: bytes) -> Size | None:
	position = 2
	while position + 9 < len(content):
		if content[position] != 0xFF:
			return None
		marker = content[position + 1]
		length = struct.unpack(">H", content[position + 2 : position + 4])[0]
		if marker in FRAMES:
			height, width = struct.unpack(">HH", content[position + 5 : position + 9])
			return (Decimal(width), Decimal(height)) if width and height else None
		position += 2 + length
	return None


def size(content: bytes) -> Size | None:
	"""Width and height of a PNG, JPEG or SVG in its own units, or None where it has no usable size."""
	if content.startswith(PNG):
		if len(content) < 24:
			return None
		width, height = struct.unpack(">II", content[16:24])
		return (Decimal(width), Decimal(height)) if width and height else None
	if content.startswith(JPEG):
		return _jpeg(content)
	return _svg(content)


def clean_svg(content: bytes) -> bytes:
	"""The SVG from its root element on, with width and height where it has a viewBox alone."""
	match = SVG_ROOT.search(content)
	if not match:
		return content
	tag = match.group(0)
	body = content[match.start() :]
	if _length(_attribute(tag, "width")) and _length(_attribute(tag, "height")):
		return body
	box = _view_box(tag)
	if not box:
		return body
	stripped = re.sub(rb"\s(width|height)\s*=\s*(['\"]).*?\2", b"", tag, flags=re.IGNORECASE | re.DOTALL)
	sized = (
		stripped[:4]
		+ b' width="%s" height="%s"' % (str(box[0]).encode(), str(box[1]).encode())
		+ stripped[4:]
	)
	return sized + content[match.end() :]


def box(proportions: Size, height: Decimal, max_width: Decimal) -> Size:
	"""Width and height in millimetres: the height of the settings, unless the width would pass max_width."""
	width, own_height = proportions
	wide = (height * width / own_height).quantize(Decimal("0.1"))
	if wide <= max_width:
		return wide, height
	return max_width, (max_width * own_height / width).quantize(Decimal("0.1"))
