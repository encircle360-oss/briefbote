"""The Auftragsbestätigung of a Sales Order: which quotation it follows, when it is delivered or performed and on
which terms it is paid. It confirms a contract and settles nothing, so it is no invoice (§ 14 Abs. 1 Satz 1 UStG)
and asks for no transfer; the invoice follows. docs/auftragsbestaetigung.md names each source.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from briefbote.invoice.document import SERVICE_PERIOD

TITLE = "Order Confirmation"
OUR_QUOTATION = "Our Quotation"
SCHEDULED_DELIVERY = "Scheduled Delivery"
SCHEDULED_DELIVERIES = "Scheduled Deliveries"
POSITION_DELIVERY = "Scheduled delivery {0}"


@dataclass(frozen=True, slots=True)
class Delivery:
	label: str
	dates: tuple[date, ...]
	per_position: bool


def delivery(
	order_date: date | None, position_dates: Iterable[date | None], period: tuple[date, date] | None = None
) -> Delivery | None:
	"""When the order is delivered or performed: the period of a service where the order has one, else the one day of
	all positions, else the span of their days with each position naming its own, else the day of the order."""
	if period:
		return Delivery(SERVICE_PERIOD, period, False)
	days = sorted({day for day in position_dates if day})
	if len(days) > 1:
		return Delivery(SCHEDULED_DELIVERIES, (days[0], days[-1]), True)
	if days:
		return Delivery(SCHEDULED_DELIVERY, (days[0],), False)
	if order_date:
		return Delivery(SCHEDULED_DELIVERY, (order_date,), False)
	return None


def quotations(names: Iterable[str | None]) -> list[str]:
	"""The quotations the positions come from, each once, in the order of the positions."""
	return list(dict.fromkeys(name for name in names if name))


@dataclass(frozen=True, slots=True)
class Term:
	"""A row of the payment schedule: its share, its amount and day as printed, the payment term and its text."""

	portion: Decimal
	amount: str
	due: str
	term: str
	description: str


PAYMENT_TERM = "Payment terms: {0}"
PAYMENT_TERMS = "Payment terms:"
TERM_TEXT = "{0}: {1}"
TERM_DUE = "{0} by {1}"


def payment_terms(terms: list[Term]) -> list[tuple[str, tuple]]:
	"""The agreed payment terms: one term by its text; several, each with its amount and its text, or its day where it
	has none. A term without any text prints nothing, so that no label stands empty."""
	if len(terms) == 1:
		text = terms[0].description or terms[0].term
		return [(PAYMENT_TERM, (text,))] if text else []
	if not terms:
		return []
	found: list[tuple[str, tuple]] = [(PAYMENT_TERMS, ())]
	for term in terms:
		text = term.description or term.term
		found.append((TERM_TEXT, (term.amount, text)) if text else (TERM_DUE, (term.amount, term.due)))
	return found


# UStAE 14.1 Abs. 17: a contract that holds every particular of § 14 Abs. 4 UStG can serve as the invoice; the
# confirmation says that the invoice is a document of its own.
INVOICE_FOLLOWS = "You will receive the invoice separately."


def closing(asks: bool) -> list[str]:
	"""The announcement of the invoice, on a valid order confirmation only (briefbote/layout/status.py)."""
	return [INVOICE_FOLLOWS] if asks else []
