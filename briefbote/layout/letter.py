"""The parts every business letter shares: the return address above the address field, the address of the recipient
and the footer with the particulars of the company.

The footer carries what a business letter of a company must state: for a GmbH the legal form, the registered office,
the register court and number, all managing directors and, where there is one, the chair of the supervisory board
(§ 35a Abs. 1 GmbHG); for an AG all members of the executive board and the chair of the supervisory board (§ 80 Abs. 1
AktG); for an Einzelkaufmann and a partnership the firm, the place, the register court and number (§ 37a Abs. 1, § 125
Abs. 1 HGB). The legal form is part of the company's name; register court and number stand as one line as they read,
„Amtsgericht Musterstadt, HRB 12345“. An invoice also needs the Steuernummer or the USt-IdNr. of the company (§ 14
Abs. 4 Satz 1 Nr. 2 UStG); the foot prints the USt-IdNr. and the Steuernummer only where there is no USt-IdNr. Every
text goes through translate, which gives it in the language of the document. docs/geschaeftsbrief.md names the
sources.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from briefbote.layout import metrics

type Translate = Callable[[str], str]

# The Anschriftzone of DIN 5008 holds six lines.
ADDRESS_LINES = 6
# About as many characters as a line of the address zone holds at 10 pt, 80 mm wide.
CHARACTERS_PER_LINE = 36


@dataclass(frozen=True, slots=True)
class Bank:
	name: str = ""
	iban: str = ""
	bic: str = ""


@dataclass(frozen=True, slots=True)
class Company:
	name: str
	street: str = ""
	street2: str = ""
	pincode: str = ""
	city: str = ""
	country: str = ""
	phone: str = ""
	email: str = ""
	website: str = ""
	registered_office: str = ""
	register_court: str = ""
	register_number: str = ""
	managing_directors: tuple[str, ...] = ()
	executive_board: tuple[str, ...] = ()
	supervisory_chair: str = ""
	vat_id: str = ""
	tax_number: str = ""
	banks: tuple[Bank, ...] = ()


@dataclass(frozen=True, slots=True)
class Party:
	name: str
	name2: str = ""
	contact: str = ""
	street: str = ""
	street2: str = ""
	pincode: str = ""
	city: str = ""
	country: str = ""


def _town(pincode: str, city: str) -> str:
	return " ".join(part for part in (pincode, city) if part)


def sender_line(company: Company) -> str:
	"""The return address in the remarks zone of the address field, one line."""
	return " · ".join(
		part for part in (company.name, company.street, _town(company.pincode, company.city)) if part
	)


# The return address: at most 7 pt, at least 6 pt, in steps of a quarter point; the width of the remarks zone of the
# address field less the indent of 5 mm on the left and 2 mm on the right.
RETURN_SIZE = Decimal(7)
RETURN_FLOOR = Decimal(6)
RETURN_STEP = Decimal("0.25")
RETURN_WIDTH = Decimal(78)


@dataclass(frozen=True, slots=True)
class ReturnAddress:
	lines: tuple[str, ...]
	size: Decimal
	fits: bool


def _sizes() -> list[Decimal]:
	steps = int((RETURN_SIZE - RETURN_FLOOR) / RETURN_STEP)
	return [RETURN_SIZE - RETURN_STEP * step for step in range(steps + 1)]


def return_address(company: Company, width: Decimal = RETURN_WIDTH) -> ReturnAddress:
	"""The return address fitted to the remarks zone: one line, set smaller down to 6 pt where it is long; then two
	lines, the name of the company above street and town, which the zone of five lines holds (DIN 5008); where even
	these pass the zone at 6 pt, the two lines at 6 pt, which do not fit."""
	line = sender_line(company)
	if not line:
		return ReturnAddress((), RETURN_SIZE, True)
	for size in _sizes():
		if metrics.width(line, size) <= width:
			return ReturnAddress((line,), size, True)
	rest = " · ".join(part for part in (company.street, _town(company.pincode, company.city)) if part)
	lines = (company.name, rest) if company.name and rest else (line,)
	for size in _sizes():
		if all(metrics.width(part, size) <= width for part in lines):
			return ReturnAddress(lines, size, True)
	return ReturnAddress(lines, RETURN_FLOOR, False)


def address_lines(party: Party, home_country: str, translate: Translate) -> list[str]:
	"""The address of the recipient, at most six lines: a foreign one ends with the country in capitals."""
	streets = [part for part in (party.street, party.street2) if part]
	country = translate(party.country).upper() if party.country and party.country != home_country else ""
	head = [part for part in (party.name, party.name2, party.contact) if part]
	tail = [part for part in (_town(party.pincode, party.city), country) if part]
	if len(head) + len(streets) + len(tail) > ADDRESS_LINES:
		streets = [", ".join(streets)]
	return [*head, *streets, *tail]


def dense(lines: list[str]) -> bool:
	"""Whether the address, wrapped at 10 pt, would run beyond the six lines of its zone, so that the print format
	sets it smaller."""
	return sum(max(1, -(-len(line) // CHARACTERS_PER_LINE)) for line in lines) > ADDRESS_LINES


def iban(number: str) -> str:
	compact = "".join(number.split()).upper()
	return " ".join(compact[index : index + 4] for index in range(0, len(compact), 4))


# The foot: at most four blocks of at most four lines, in equal columns of the type area at 6.8 pt, each column
# with a gutter of 2.5 mm before the next.
FOOT_LINES = 4
FOOT_SIZE = Decimal("6.8")
FOOT_WIDTH = Decimal(175)
FOOT_GUTTER = Decimal("2.5")
NO_BREAK = "\u00a0"
# How far a whole IBAN may reach beyond its column by measure, in millimetres; the reserve of the measure covers it.
IBAN_SLACK = Decimal(1)


def _foot_width(text: str) -> Decimal:
	"""The width of a line of the foot by the advance widths of Inter: both PDF generators set the foot at these
	widths, as the lines of the printouts of the proof measure, and the proof checks every foot against the lines
	this width predicts."""
	return metrics.width(text, FOOT_SIZE) / metrics.RESERVE


def wrapped_lines(lines: list[str], column: Decimal) -> int:
	"""How many lines the block takes in a column of the width in millimetres, where a long line wraps at its spaces
	and never at a no-break space; a part wider than the column stands alone and overflows. The measure is
	_foot_width, without the reserve of briefbote/layout/metrics.py."""
	room = column - FOOT_GUTTER
	count = 0
	for line in lines:
		current = ""
		count += 1
		for part in line.split(" "):
			candidate = f"{current} {part}" if current else part
			if current and _foot_width(candidate) > room:
				count += 1
				current = part
			else:
				current = candidate
	return count


FOOT_BLOCKS = ("Name and Address", "Contact", "Register and Management", "Tax and Bank")


def foot_blocks(company: Company, translate: Translate) -> list[list[str]]:
	"""The lines of the blocks of the foot, without the empty ones (_foot)."""
	return [block for _name, block in _foot(company, translate)]


def foot_overflows(company: Company, translate: Translate) -> list[tuple[str, int]]:
	"""Each block of the foot that needs more than four lines in its column, by its name in FOOT_BLOCKS, with the
	lines it needs; the fifth runs into the gap above the page line."""
	named = _foot(company, translate)
	column = FOOT_WIDTH / max(len(named), 1)
	return [(name, lines) for name, block in named if (lines := wrapped_lines(block, column)) > FOOT_LINES]


def _foot(company: Company, translate: Translate) -> list[tuple[str, list[str]]]:
	"""The particulars of the company in the blocks of the foot, without empty ones: name and address; contact;
	register and management; tax and bank, the Steuernummer only where there is no USt-IdNr., the first bank
	account.

	Two particulars joined by a separator, court and number, bank and BIC, share a line where they fit its column;
	else each takes a line of its own, so that no separator ends or starts a line. The names of the management are a
	comma-separated list that wraps like running text. The registered office always stands in the foot (§ 35a Abs. 1 GmbHG): in register and management, or,
	where that block would need more than four lines, under the address. Tax and bank, where it would need more
	than four lines, hands the USt-IdNr. to register and management where that keeps four lines, else leaves out the
	name of the bank, which the BIC names. A name of the management never breaks; its line breaks after the label
	and after a comma."""
	address = [
		line
		for line in (company.name, company.street, company.street2, _town(company.pincode, company.city))
		if line
	]
	contact = [
		line
		for line in (
			translate("Phone {0}").format(company.phone) if company.phone else "",
			company.email,
			company.website,
		)
		if line
	]
	bank = company.banks[0] if company.banks else None
	vat = translate("VAT ID: {0}").format(company.vat_id) if company.vat_id else ""
	tax_number = (
		translate("Tax Number: {0}").format(company.tax_number) if company.tax_number and not vat else ""
	)
	has_taxes = bool(vat or tax_number or bank)
	directors = company.managing_directors
	register_present = any(
		(
			company.registered_office,
			company.register_court,
			company.register_number,
			directors,
			company.executive_board,
			company.supervisory_chair,
		)
	)
	count = sum(1 for present in (address, contact, register_present, has_taxes) if present)
	column = FOOT_WIDTH / max(count, 1)
	office = (
		translate("Registered Office: {0}").format(company.registered_office)
		if company.registered_office
		else ""
	)
	register = [
		office,
		*_joined(
			", ", tuple(_whole(part) for part in (company.register_court, company.register_number)), column
		),
		*_listed(
			translate("Managing Directors:" if len(directors) > 1 else "Managing Director:"),
			directors,
			column,
		),
		*_listed(translate("Executive Board:"), company.executive_board, column),
		translate("Chair of the Supervisory Board: {0}").format(company.supervisory_chair)
		if company.supervisory_chair
		else "",
	]
	register = [line for line in register if line]
	if (
		office
		and wrapped_lines(register, column) > FOOT_LINES
		and wrapped_lines([*address, office], column) <= FOOT_LINES
	):
		register.remove(office)
		address.append(office)
	bic = f"BIC{NO_BREAK}{bank.bic}" if bank and bank.bic else ""
	bank_lines = _joined(" · ", (bank.name, bic), column) if bank else []
	iban = [_iban_line(bank.iban, column)] if bank and bank.iban else []
	taxes = [line for line in (vat, tax_number, *bank_lines, *iban) if line]
	if wrapped_lines(taxes, column) > FOOT_LINES and bank:
		if vat and wrapped_lines([*register, vat], column) <= FOOT_LINES:
			register.append(vat)
			taxes.remove(vat)
		elif bank.name and bic:
			taxes = [line for line in (vat, tax_number, bic, *iban) if line]
	blocks = zip(FOOT_BLOCKS, (address, contact, register, taxes), strict=True)
	return [(name, block) for name, block in blocks if block]


def _fits(line: str, column: Decimal) -> bool:
	return _foot_width(line) <= column - FOOT_GUTTER


def _joined(separator: str, parts: tuple[str, ...], column: Decimal) -> list[str]:
	"""Two particulars on one line where they fit, bound to each other so that the separator neither ends nor starts
	a line; else one a line, without the separator."""
	present = [part for part in parts if part]
	line = separator.replace(" ", NO_BREAK).join(_whole(part) for part in present)
	return [line] if _fits(line, column) else present


def _listed(label: str, names: tuple[str, ...], column: Decimal) -> list[str]:
	"""A label and its names, comma-separated, in one line that wraps over the width of the block after the label
	and after a comma, never inside a name."""
	return [f"{label} {', '.join(_whole(name) for name in names)}"] if names else []


def _iban_line(number: str, column: Decimal) -> str:
	"""The IBAN in groups of four, whole where it about fits its column, as a German one in a quarter of the type
	area, else wrapped between two groups, never inside one."""
	line = f"IBAN {iban(number)}"
	if metrics.width(line, FOOT_SIZE) <= column * metrics.RESERVE + IBAN_SLACK:
		return line.replace(" ", NO_BREAK)
	first, _space, rest = line.partition(" ")
	head, _space, tail = rest.partition(" ")
	return f"{first}{NO_BREAK}{head} {tail}".strip()


def _whole(text: str) -> str:
	"""The text with no-break spaces, so that a narrow column wraps a line between its parts and not inside one."""
	return text.replace(" ", NO_BREAK)


# „vom“ or „of“ before a placeholder introduces the date of a document, „zum Lieferschein LS-1 vom 23.11.2026“.
DATE_INTRODUCED = re.compile(r" (vom|of) \{")


def dates_together(text: str) -> str:
	"""A text of a printout with „vom“ or „of“ joined to the date after it by a no-break space, so that a heading,
	a sentence or a running title breaks before „vom“ if at all, never between it and its date."""
	return DATE_INTRODUCED.sub(lambda found: f" {found.group(1)}\N{NO-BREAK SPACE}{{", text)
