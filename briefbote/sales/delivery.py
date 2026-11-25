"""The Lieferschein of a Delivery Note: whether it prints prices, how it names serial numbers and batches, and the
dates it states. No law prescribes its content; an invoice may take the day of the supply from a delivery note it
names, where the note states that day beside its own date (UStAE 14.5 Abs. 16, § 31 Abs. 1 UStDV). A delivery note
settles nothing and is no invoice (§ 14 Abs. 1 Satz 1 UStG). docs/lieferschein.md names each source.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

TITLE = "Delivery Note"
RETURN_TITLE = "Return Delivery Note"


def title(is_return: bool) -> str:
	return RETURN_TITLE if is_return else TITLE


def prices(setting: bool, without_amount: bool) -> bool:
	"""Prices only where the Einstellungen Geschäftspost ask for them and the note itself does not leave them out
	(print_without_amount of ERPNext)."""
	return setting and not without_amount


DATE = "Date"
DELIVERY_DATE = "Delivery Date"


def dates(posting_date: date) -> list[tuple[str, date]]:
	"""The date of the note and the day of delivery, which ERPNext keeps as one: the posting date of the note."""
	return [(DATE, posting_date), (DELIVERY_DATE, posting_date)]


@dataclass(frozen=True, slots=True)
class Batch:
	name: str
	quantity: Decimal


SERIAL_NUMBER = "Serial number: {0}"
SERIAL_NUMBERS = "Serial numbers: {0}"
BATCH = "Batch: {0}"
BATCHES = "Batches: {0}"


def split_serials(text: str | None) -> list[str]:
	"""The serial numbers of the text field of a row, one per line."""
	return [line.strip() for line in (text or "").splitlines() if line.strip()]


def number(value: Decimal) -> str:
	"""A quantity or weight as German print shows it: 2,5, never 2,500."""
	text = format(value.normalize(), "f")
	return text.replace(".", ",")


def identifiers(serials: Iterable[str], batches: Iterable[Batch]) -> list[tuple[str, tuple[str]]]:
	"""The serial numbers and the batches of a position, each once; several batches with the quantity of each."""
	found: list[tuple[str, tuple[str]]] = []
	numbers = list(dict.fromkeys(serial for serial in serials if serial))
	if numbers:
		found.append((SERIAL_NUMBERS if len(numbers) > 1 else SERIAL_NUMBER, (", ".join(numbers),)))
	quantities: dict[str, Decimal] = {}
	for batch in batches:
		if batch.name:
			quantities[batch.name] = quantities.get(batch.name, Decimal(0)) + abs(batch.quantity)
	if len(quantities) > 1:
		listed = ", ".join(f"{name} ({number(quantity)})" for name, quantity in quantities.items())
		found.append((BATCHES, (listed,)))
	elif quantities:
		found.append((BATCH, (next(iter(quantities)),)))
	return found


RECEIVED = "Goods received"
SIGNATURE_FIELDS = ("Date", "Signature", "Name in block capitals")
NET_WEIGHT = "Total net weight: {0}"
OUR_ORDER = "Our Order"


def asks_signature(setting: bool, submitted: bool) -> bool:
	"""The line for the signature of the recipient, where the settings ask for it, on a submitted note only: a draft
	or a cancelled note asks nobody to confirm a receipt."""
	return setting and submitted
