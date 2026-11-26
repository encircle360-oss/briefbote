"""The parts of a business letter beyond its text: the recipient, the information block, the page line and what keeps
the letter from being sent. docs/geschaeftsbrief-format.md names the sources.

The address field holds the organisation in its first line and the person below it, a private person alone in the
first line; an address abroad ends with the country in capitals (DIN 5008, briefbote/layout/letter.py). The
information block holds the items of DIN 5008 that the letter has, in the order of the standard: Unser Zeichen, the
person to contact with phone and e-mail, the date last. A letter needs a postal address and a text; a subject is
usual but not required, so a missing one is a warning on saving and no finding on paper.
"""

from collections.abc import Callable
from decimal import Decimal

from briefbote.layout import letter as letters
from briefbote.layout import metrics

type Translate = Callable[[str], str]

OUR_REFERENCE = "Our Reference"
DEPARTMENT = "Department"
NAME = "Name"
PHONE = "Phone"
EMAIL = "Email"
DATE = "Date"
ADDRESSED = "Letter to {0} dated {1}"
UNADDRESSED = "Letter dated {0}"
FINDINGS_TITLE = "This letter is incomplete and must not be sent like this:"
NO_ADDRESS = (
	"The letter has no postal address of its recipient: choose an address with street, postcode and town."
)
EMPTY_BODY = "The letter has no text."
NO_SUBJECT = "The letter has no subject. DIN 5008 does not require one, but a subject tells the recipient at a glance what the letter is about."
# The information block (style.html): 75 mm wide at 8.5 pt, the labels as wide as the longest, 4 mm before the values.
INFO_WIDTH = Decimal(75)
INFO_SIZE = Decimal("8.5")
LABEL_GAP = Decimal(4)
# The longest name of the recipient the page line holds, in characters.
TITLE_NAME = 40


def party(
	organisation: str,
	person: str,
	street: str = "",
	street2: str = "",
	pincode: str = "",
	city: str = "",
	country: str = "",
) -> letters.Party:
	"""The recipient: the organisation, then the person where it differs; a person without organisation first."""
	return letters.Party(
		name=organisation or person,
		contact=person if organisation and person != organisation else "",
		street=street,
		street2=street2,
		pincode=pincode,
		city=city,
		country=country,
	)


def lines(recipient: letters.Party, home_country: str, translate: Translate) -> list[str]:
	return letters.address_lines(recipient, home_country, translate)


def postal(recipient: letters.Party) -> bool:
	"""Whether the address reaches the recipient by post: a street and a postcode or town."""
	return bool(recipient.street and (recipient.pincode or recipient.city))


def information(
	translate: Translate,
	reference: str = "",
	department: str = "",
	name: str = "",
	phone: str = "",
	email: str = "",
	date: str = "",
) -> list[tuple[str, str]]:
	"""The rows of the information block that have a value; phone and e-mail only with the person they reach."""
	rows = [
		(OUR_REFERENCE, reference),
		(DEPARTMENT, department),
		(NAME, name),
		(PHONE, phone if name else ""),
		(EMAIL, email if name else ""),
		(DATE, date),
	]
	return _fitted([(translate(label), value) for label, value in rows if value])


def _fitted(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
	"""The rows with a value wider than the column of the values broken into rows of their own: between its words,
	so that the browser does not break a number at a hyphen, and an e-mail address before its @."""
	column = (
		INFO_WIDTH - LABEL_GAP - max((metrics.width(label, INFO_SIZE) for label, _value in rows), default=0)
	)
	found = []
	for label, value in rows:
		lines = _wrapped(value, column)
		found += [(label if index == 0 else "", line) for index, line in enumerate(lines)]
	return found


def _wrapped(value: str, column: Decimal) -> list[str]:
	if metrics.width(value, INFO_SIZE) <= column:
		return [value]
	local, at, domain = value.partition("@")
	if at and " " not in value:
		return [local, at + domain]
	lines: list[str] = []
	for word in value.split(" "):
		if lines and metrics.width(f"{lines[-1]} {word}", INFO_SIZE) <= column:
			lines[-1] = f"{lines[-1]} {word}"
		else:
			lines.append(word)
	return lines


def running_title(recipient: str, date: str, translate: Translate) -> str:
	"""The title of the page line, so that a page that comes loose can be put back: to whom and of which day."""
	if not recipient:
		return translate(UNADDRESSED).format(date)
	if len(recipient) > TITLE_NAME:
		cut = recipient[:TITLE_NAME]
		recipient = (cut.rsplit(" ", 1)[0] if " " in cut else cut) + "…"
	return translate(ADDRESSED).format(recipient, date)


def findings(postal: bool, text: bool) -> list[str]:
	"""What keeps the letter from being sent."""
	return [found for found, missing in ((NO_ADDRESS, not postal), (EMPTY_BODY, not text)) if missing]


def warns_without_subject(subject: str | None) -> bool:
	return not (subject or "").strip()
