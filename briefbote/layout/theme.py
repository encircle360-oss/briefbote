"""The look of a company's printouts, set in the Einstellungen Geschäftspost: an accent colour for the heads of the
tables and the rules, the place and size of the logo, the columns of the footer and the font. Everything a template
takes from here is checked first, so that a setting can never put CSS of its own into a printout.
"""

import re

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


# The least contrast of small text against white paper, WCAG 2.2, success criterion 1.4.3.
READABLE = 4.5


def _luminance(value: str) -> float:
	"""The relative luminance of a colour #RRGGBB (WCAG 2.2)."""

	def channel(digits: str) -> float:
		component = int(digits, 16) / 255
		return component / 12.92 if component <= 0.04045 else ((component + 0.055) / 1.055) ** 2.4

	red, green, blue = (channel(value[index : index + 2]) for index in (1, 3, 5))
	return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(value: str) -> float:
	"""The contrast of a colour #RRGGBB against white."""
	return 1.05 / (_luminance(value) + 0.05)


def text_colour(accent: str) -> str:
	"""The colour of small text that takes the accent, such as the heads of the tables: the accent where it reads
	against white with a contrast of at least 4.5:1, else the accent darkened step by step towards black, so that it
	keeps its hue. Rules and marks keep the accent itself."""
	shade = accent
	steps = 0
	while contrast(shade) < READABLE:
		steps += 1
		factor = 1 - steps / 20
		shade = "#" + "".join(
			f"{round(int(accent[index : index + 2], 16) * factor):02X}" for index in (1, 3, 5)
		)
	return shade


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
