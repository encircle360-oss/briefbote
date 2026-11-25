"""The geometry of a business letter on A4 by DIN 5008 (Schreib- und Gestaltungsregeln für die Text- und
Informationsverarbeitung, edition 2020-03), in millimetres from the top left corner of the sheet.

Form A has a letterhead of 27 mm, form B one of 45 mm; both put the address field of 85 x 45 mm 20 mm from the left
edge, which fits the window of the envelopes C5/6, DL and C4 of DIN 680. The address field has a zone of five lines
for remarks and the return address above a zone of six lines for the address (17.7 mm and 27.3 mm at 4.23 mm a line,
DIN 5008 table „Anschriftfeld“). The fold marks fold the sheet for the window; the punch mark halves it. The text runs
25 mm from the left, so that a line of the address starts where the lines of the body start: 5 mm inside the address
field. The information block starts 125 mm from the left and is at most 75 mm wide, which ends it 10 mm from the
right edge, the least right margin the sources name; the text ends there too, so that information block, logo,
table and footer share one right edge. docs/din-5008.md names the sources and what they say.
"""

from dataclasses import dataclass

PAGE = (210, 297)
MARGIN_LEFT = 25
MARGIN_RIGHT = 10
TEXT_WIDTH = PAGE[0] - MARGIN_LEFT - MARGIN_RIGHT
ADDRESS_INSET = 5
REMARK_ZONE_HEIGHT = 17.7
ADDRESS_ZONE_HEIGHT = 27.3
PUNCH_MARK = 148.5
INFORMATION_LEFT = 125
INFORMATION_WIDTH = PAGE[0] - MARGIN_RIGHT - INFORMATION_LEFT


@dataclass(frozen=True, slots=True)
class Box:
	left: float
	top: float
	width: float
	height: float

	@property
	def right(self) -> float:
		return self.left + self.width

	@property
	def bottom(self) -> float:
		return self.top + self.height

	def holds(self, left: float, top: float, right: float, bottom: float, tolerance: float = 0) -> bool:
		"""Whether a rectangle lies inside this one, reaching over an edge by no more than the tolerance."""
		return (
			left >= self.left - tolerance
			and top >= self.top - tolerance
			and right <= self.right + tolerance
			and bottom <= self.bottom + tolerance
		)


@dataclass(frozen=True, slots=True)
class Form:
	name: str
	letterhead_height: float
	address: Box
	information: Box
	fold_marks: tuple[float, float]

	@property
	def remarks(self) -> Box:
		"""The Zusatz- und Vermerkzone: the return address and remarks such as the kind of dispatch."""
		return Box(self.address.left, self.address.top, self.address.width, REMARK_ZONE_HEIGHT)

	@property
	def recipient(self) -> Box:
		"""The Anschriftzone: the recipient, at most six lines."""
		return Box(
			self.address.left, self.address.top + REMARK_ZONE_HEIGHT, self.address.width, ADDRESS_ZONE_HEIGHT
		)


FORMS = {
	"A": Form(
		name="A",
		letterhead_height=27,
		address=Box(left=20, top=27, width=85, height=45),
		information=Box(left=INFORMATION_LEFT, top=32, width=INFORMATION_WIDTH, height=40),
		fold_marks=(87, 192),
	),
	"B": Form(
		name="B",
		letterhead_height=45,
		address=Box(left=20, top=45, width=85, height=45),
		information=Box(left=INFORMATION_LEFT, top=50, width=INFORMATION_WIDTH, height=40),
		fold_marks=(105, 210),
	),
}


def form(name: str | None) -> Form:
	"""The form by its letter, as the settings name it („A“, „Form A“); form B where none is chosen, the form most
	letters use."""
	letter = (name or "B").strip()[-1:].upper()
	return FORMS.get(letter, FORMS["B"])
