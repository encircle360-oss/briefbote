"""The parts of a business letter beyond its text: the recipient, the information block, the page line and what keeps
the letter from being sent. docs/geschaeftsbrief-format.md names the sources.

The address field holds the organisation in its first line and the person below it, a private person alone in the
first line; an address abroad ends with the country in capitals (DIN 5008, briefbote/layout/letter.py). The
information block holds the items of DIN 5008 that the letter has, in the order of the standard: Unser Zeichen, the
person to contact with phone and e-mail, the date last. A letter needs a postal address and a text; a subject is
usual but not required, so a missing one is a warning on saving and no finding on paper.
"""

from collections.abc import Callable

from briefbote.layout import letter as letters

type Translate = Callable[[str], str]

OUR_REFERENCE = "Our Reference"
DEPARTMENT = "Department"
NAME = "Name"
PHONE = "Phone"
EMAIL = "Email"
DATE = "Date"
ADDRESSED = "Letter to {0} of {1}"
UNADDRESSED = "Letter of {0}"
FINDINGS_TITLE = "This letter is incomplete and must not be sent like this:"
NO_ADDRESS = (
	"The letter has no postal address of its recipient: choose an address with street, postcode and town."
)
EMPTY_BODY = "The letter has no text."
NO_SUBJECT = "The letter has no subject. DIN 5008 does not require one, but a subject tells the recipient at a glance what the letter is about."
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
	return [(translate(label), value) for label, value in rows if value]


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
