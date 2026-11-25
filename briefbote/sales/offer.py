"""The Angebot of a Quotation: which of its positions count toward the total, what an alternative or a unit price
says, and until when and how the customer accepts it. An offer is no invoice (§ 14 Abs. 1 Satz 1 UStG: a document by
which a supply is settled); it asks for no payment. docs/angebot.md names each source.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

TITLE = "Quotation"


class Role(StrEnum):
	POSITION = "position"
	ALTERNATIVE = "alternative"
	UNIT_PRICE = "unit price"


@dataclass(frozen=True, slots=True)
class Row:
	name: str
	number: int
	alternative: bool = False
	quantity: Decimal = Decimal(1)


@dataclass(frozen=True, slots=True)
class Line:
	name: str
	role: Role
	replaces: int | None = None

	@property
	def counts(self) -> bool:
		return self.role is Role.POSITION


ALTERNATIVE = "Alternative to position {0}, not included in the total."
ALTERNATIVE_ALONE = "Alternative position, not included in the total."
UNIT_PRICE = "Price per unit, billed by the quantity supplied and not included in the total."


def lines(rows: Iterable[Row]) -> list[Line]:
	"""The role of each row. ERPNext keeps an alternative right after the position it may replace, marks that position
	(set_has_alternative_item in erpnext/selling/doctype/quotation/quotation.py) and leaves alternatives out of the
	totals (filter_rows in erpnext/controllers/taxes_and_totals.py). A row with a quantity of 0 offers a price for each
	unit where the Selling Settings allow it (allow_zero_qty_in_quotation)."""
	found, replaced = [], None
	for row in rows:
		if row.alternative:
			found.append(Line(row.name, Role.ALTERNATIVE, replaced))
			continue
		replaced = row.number
		found.append(Line(row.name, Role.POSITION if row.quantity else Role.UNIT_PRICE))
	return found


def note(line: Line) -> tuple[str, tuple] | None:
	"""What a row that does not count says of itself, so that no reader adds it to the total."""
	if line.role is Role.ALTERNATIVE:
		return (ALTERNATIVE, (line.replaces,)) if line.replaces else (ALTERNATIVE_ALONE, ())
	if line.role is Role.UNIT_PRICE:
		return UNIT_PRICE, ()
	return None


VALID_UNTIL = "Valid Until"
# § 148 BGB: where the offeror sets a period for acceptance, the offer can only be accepted within it.
VALID_UNTIL_ACCEPT = "This quotation is valid until {0}. To accept it, please confirm it to us by then in writing or by e-mail, stating its number."
# § 147 Abs. 2 BGB: without a period, an offer stands as long as an answer may be expected under usual circumstances.
ACCEPT = "To accept this quotation, please confirm it to us in writing or by e-mail, stating its number."


def closing(valid_till: date | None, submitted: bool = True) -> list[tuple[str, tuple]]:
	"""Until when the quotation stands and how the customer accepts it; nothing for a draft or a cancelled quotation,
	which is no offer to accept."""
	if not submitted:
		return []
	if valid_till:
		return [(VALID_UNTIL_ACCEPT, (valid_till,))]
	return [(ACCEPT, ())]
