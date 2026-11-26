"""The Anzahlungsrechnung: an invoice over a payment before the supply (§ 14 Abs. 5 Satz 1 UStG), printed from the
copy of a Sales Order that a Proforma Invoice of ERPNext 16 renders. docs/anzahlungsrechnung.md names each source.

UStAE 14.8 Abs. 1 Satz 1: the invoice shows that it bills an advance, for instance by the expected time of the supply.
Abs. 4: § 14 Abs. 4 UStG applies accordingly; instead of the time of the supply the invoice states its expected time
or calendar month (§ 31 Abs. 4 UStDV), the agreed period or deadline, or that none is agreed yet; instead of the
consideration of the supply the consideration billed in advance, and the tax on it. Abs. 5 Satz 3: it may be issued
before the payment is received; the tax arises only on what is received (Satz 4, § 13 Abs. 1 Nr. 1 Buchst. a Satz 4
UStG).
"""

from collections.abc import Iterable
from datetime import date

TITLE = "Advance Invoice"
SUBJECT = "Advance Invoice {0} for Order {1}"
SUBJECT_UNNUMBERED = "Advance Invoice for Order {0}"
ORDER = "Order"
# The labels of the time of the supply, as the invoice has them; the value says that it is expected.
EXPECTED_DATE = "Service Date"
EXPECTED_PERIOD = "Service Period"
EXPECTED = "expected {0}"
RECEIVED = "Date of Receipt"
ADVANCE = "This invoice bills an advance payment before the supply or service is rendered (Section 14(5) sentence 1 UStG)."
NOT_AGREED = "The time of the supply or service has not been agreed yet."
REQUEST = "Please transfer {0} to the account below, stating the invoice number."
NO_NUMBER = (
	"This document has no invoice number of its own (Section 14(4) sentence 1 no. 4 UStG): print the advance invoice "
	"from a Proforma Invoice of the order."
)
TEXTS = (
	TITLE,
	SUBJECT,
	SUBJECT_UNNUMBERED,
	ORDER,
	EXPECTED_DATE,
	EXPECTED_PERIOD,
	EXPECTED,
	RECEIVED,
	ADVANCE,
	NOT_AGREED,
	REQUEST,
	NO_NUMBER,
)


def expected(
	period: tuple[date, date] | None, order_date: date | None, position_dates: Iterable[date | None]
) -> tuple[str, tuple[date, ...]] | None:
	"""The expected time of the supply: the period of the order, else the day or span of the days of its positions,
	else the day of delivery of the order; None where nothing is agreed."""
	if period:
		return EXPECTED_PERIOD, period
	days = sorted({day for day in position_dates if day})
	if len(days) > 1:
		return EXPECTED_PERIOD, (days[0], days[-1])
	if days:
		return EXPECTED_DATE, (days[0],)
	if order_date:
		return EXPECTED_DATE, (order_date,)
	return None


def notices(when: tuple[str, tuple[date, ...]] | None) -> list[str]:
	"""That the invoice bills an advance, and that the time of the supply is not agreed where it is not."""
	return [ADVANCE] if when else [ADVANCE, NOT_AGREED]


def received(issued: date, days: Iterable[date]) -> date | None:
	"""The day the advance was received, where it is certain: the one payment of its amount on the order, received
	before the day of the invoice (§ 14 Abs. 4 Satz 1 Nr. 6 UStG)."""
	found = sorted(set(days))
	if len(found) == 1 and found[0] < issued:
		return found[0]
	return None


def findings(numbered: bool) -> list[str]:
	return [] if numbered else [NO_NUMBER]


def request(numbered: bool, asks: bool, account: bool) -> str:
	"""The request to pay the advance: only on a numbered invoice that is neither a draft nor cancelled and has an
	account to pay to."""
	return REQUEST if numbered and asks and account else ""


def subject(number: str, order: str) -> tuple[str, tuple]:
	if number:
		return SUBJECT, (number, order)
	return SUBJECT_UNNUMBERED, (order,)
