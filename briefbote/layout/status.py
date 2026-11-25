"""The mark of a document that is not, or no longer, valid: a draft (docstatus 0 of a submittable DocType) and a
cancelled document (docstatus 2). Each page carries the word across it and in the page line, so that a printout
can never pass for the final or a valid document; neither asks for payment. Frappe prints them at all only where
the Print Settings allow it (Allow Print for Draft, Allow Print for Cancelled; validate_print_for_docstatus in
frappe/www/printview.py). Other states, such as paid or overdue, change after printing and get no mark.
"""

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Status:
	name: str
	# The word across the page and the word in the page line, in English; the print formats translate both.
	mark: str
	label: str


DRAFT = Status("draft", "DRAFT", "Draft")
CANCELLED = Status("cancelled", "CANCELLED", "Cancelled")


def of(submittable: bool, docstatus: int) -> Status | None:
	if not submittable:
		return None
	return {0: DRAFT, 2: CANCELLED}.get(docstatus)


def asks_for_payment(found: Status | None) -> bool:
	return found is None


CAPITALS = Path(__file__).resolve().parent / "inter_semibold_capitals.json"
# The mark across a page: its size in millimetres, its angle and its grey, translucent so that the text beneath
# stays readable and dark enough for a print in black and white.
MARK_SIZE = 30
MARK_ANGLE = -40
MARK_OPACITY = 0.14


@cache
def _capitals() -> dict:
	return json.loads(CAPITALS.read_text(encoding="utf-8"))


def svg(word: str, width: float, height: float) -> str:
	"""The mark as an SVG of the given size in millimetres: the word in the capitals of Inter as paths, rotated
	about the middle, so that it needs no font where a PDF generator draws it as an image."""
	table = _capitals()
	scale = MARK_SIZE / table["units_per_em"]
	glyphs = table["glyphs"]
	x, paths = 0, []
	for letter in word.upper():
		glyph = glyphs.get(letter)
		if glyph is None:
			x += glyphs["M"]["advance"]
			continue
		paths.append(f'<path transform="translate({x} 0)" d="{glyph["path"]}"/>')
		x += glyph["advance"]
	left = width / 2 - x * scale / 2
	baseline = height / 2 + table["cap_height"] * scale / 2
	return (
		f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}mm" '
		f'height="{height}mm"><g fill="#000" fill-opacity="{MARK_OPACITY}" '
		f'transform="rotate({MARK_ANGLE} {width / 2} {height / 2}) translate({left:.2f} {baseline:.2f}) '
		f'scale({scale:.6f} -{scale:.6f})">{"".join(paths)}</g></svg>'
	)
