"""The width of a line of text in the regular weight of Inter, from the advance widths of its glyphs
(inter_regular_widths.json, written by scripts/build_fonts.py).

The measure leaves out kerning, which narrows a line, and adds a reserve for a font of the system, whose letters may
run wider, and for the rendering of a PDF generator, which rounds each glyph."""

import json
from decimal import Decimal
from functools import cache
from pathlib import Path

TABLE = Path(__file__).resolve().parent / "inter_regular_widths.json"
POINT_MM = Decimal("25.4") / 72
RESERVE = Decimal("1.06")
# A character the font lacks counts as wide as the letter M.
FALLBACK = "M"


@cache
def _table() -> tuple[int, dict[str, int]]:
	data = json.loads(TABLE.read_text(encoding="utf-8"))
	return data["units_per_em"], data["advances"]


def width(text: str, size_pt: Decimal, reserve: bool = True) -> Decimal:
	"""The width of the text in millimetres at the size in points, with the reserve unless asked without, for text
	that is set in the embedded Inter alone."""
	units_per_em, advances = _table()
	units = sum(advances.get(char, advances[FALLBACK]) for char in text)
	return Decimal(units) / units_per_em * size_pt * POINT_MM * (RESERVE if reserve else 1)
