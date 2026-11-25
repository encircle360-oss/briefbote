"""The look of a company's printouts, set in the Einstellungen Geschäftspost: an accent colour for the heads of the
tables and the rules, the place and size of the logo, the columns of the footer and the font. Everything a template
takes from here is checked first, so that a setting can never put CSS of its own into a printout.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

BLACK = "#111111"
HEX = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
LOGO_HEIGHT = 20
LOGO_MINIMUM = 8
# Space between the logo and the address field, in millimetres.
LOGO_CLEARANCE = 4
EMBEDDED = "Inter (embedded)"
SYSTEM = "System sans-serif"
SYSTEM_STACK = '"Nimbus Sans", "Liberation Sans", Arial, Helvetica, sans-serif'


def colour(value: str | None) -> str:
	"""A colour as #RRGGBB, black for anything that is no hexadecimal colour."""
	match = HEX.fullmatch((value or "").strip())
	if not match:
		return BLACK
	digits = match.group(1)
	if len(digits) == 3:
		digits = "".join(digit * 2 for digit in digits)
	return f"#{digits.upper()}"


def logo_side(value: str | None) -> str:
	return "left" if value == "Left" else "right"


def logo_height(value: float | None, letterhead: float, top: float) -> float:
	"""The height of the logo in millimetres, within the letterhead above the address field."""
	room = letterhead - top - LOGO_CLEARANCE
	wanted = value or LOGO_HEIGHT
	return min(max(wanted, LOGO_MINIMUM), room)


def embeds(font: str | None) -> bool:
	return font != SYSTEM


def font_stack(font: str | None) -> str:
	return SYSTEM_STACK if not embeds(font) else f'"Inter Tabular", {SYSTEM_STACK}'


class Block(StrEnum):
	"""The blocks of the footer (briefbote/layout/letter.py, footer_blocks)."""

	COMPANY = "Company and Contact"
	REGISTER = "Register and Management"
	TAXES = "Tax Numbers"
	BANK = "Bank Accounts"


def block(name: str) -> Block:
	return Block(name)


@dataclass(frozen=True, slots=True)
class Placement:
	column: int
	block: Block


def arrange(blocks: dict[Block, list[str]], layout: tuple[Placement, ...]) -> list[list[str]]:
	"""The columns of the footer: without a layout each block is a column of its own in the order of Block; with one,
	the blocks stand in the columns it names, stacked in its order. Empty columns drop out."""
	if not layout:
		layout = tuple(Placement(index, name) for index, name in enumerate(Block, start=1))
	columns: dict[int, list[str]] = defaultdict(list)
	for placement in layout:
		columns[placement.column] += blocks.get(placement.block, [])
	return [columns[number] for number in sorted(columns) if columns[number]]
