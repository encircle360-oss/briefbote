"""The statement of a customer's or supplier's account as of a cut-off date: its open items as ERPNext's reports
Accounts Receivable and Accounts Payable return them, read from the Payment Ledger, and the balance of each currency.
Briefbote calculates no open item of its own; it sorts the rows of the report, adds them up per currency and names
the side the balance is in favour of. A draft reads the ledger each time it is printed; a submitted document prints
the rows it stored when it was submitted, so that a statement that went out reprints as it was sent.
docs/kontoauszug.md and docs/saldenbestaetigung.md name the sources.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

OPEN_ITEMS = "Open Items"
BALANCE_CONFIRMATION = "Balance Confirmation"
_SERIES = {OPEN_ITEMS: "KA-.YYYY.-.####", BALANCE_CONFIRMATION: "SB-.YYYY.-.####"}
STATEMENT_TITLE = "Statement of Account"
CONFIRMATION_TITLE = "Balance Confirmation"
_TITLES = {OPEN_ITEMS: STATEMENT_TITLE, BALANCE_CONFIRMATION: CONFIRMATION_TITLE}


def series(kind: str) -> str:
	return _SERIES[kind]


def title(kind: str) -> str:
	return _TITLES[kind]


def reads_ledger(docstatus: int) -> bool:
	"""Whether the document shows the ledger as it is now, which only a draft does."""
	return docstatus == 0


def states(kind: str, printed_kind: str, docstatus: int) -> bool:
	"""Whether a print format of printed_kind states a balance: a draft or submitted document of its kind, not a
	cancelled one and not one of the other kind."""
	return kind == printed_kind and docstatus in (0, 1)


INVOICE = "Invoice"
CORRECTION = "Correction"
PAYMENT = "Payment"
BOOKING = "Booking"
OTHER = "Document"
_KINDS = {
	"Sales Invoice": INVOICE,
	"Purchase Invoice": INVOICE,
	"Payment Entry": PAYMENT,
	"Journal Entry": BOOKING,
}


@dataclass(frozen=True, slots=True)
class Item:
	voucher_type: str
	voucher_no: str
	kind: str
	# The partner's own number of the voucher: the supplier's invoice number, the customer's order number.
	reference: str
	posting_date: date | None
	due_date: date | None
	invoiced: Decimal
	paid: Decimal
	outstanding: Decimal
	currency: str


def _amount(value) -> Decimal:
	return Decimal(str(value or 0))


def item(row: Mapping) -> Item:
	"""One row of the report: invoiced, paid and outstanding as the report has them, credit notes counted as paid."""
	voucher_type = row.get("voucher_type") or ""
	kind = CORRECTION if row.get("is_return") else _KINDS.get(voucher_type, OTHER)
	return Item(
		voucher_type=voucher_type,
		voucher_no=row.get("voucher_no") or "",
		kind=kind,
		reference=row.get("bill_no") or row.get("po_no") or "",
		posting_date=row.get("posting_date"),
		due_date=row.get("due_date"),
		invoiced=_amount(row.get("invoiced")),
		paid=_amount(row.get("paid")) + _amount(row.get("credit_note")),
		outstanding=_amount(row.get("outstanding")),
		currency=row.get("currency") or "",
	)


def items(rows: Iterable[Mapping]) -> list[Item]:
	found = [item(row) for row in rows if row and row.get("voucher_no")]
	return sorted(found, key=lambda found: (found.posting_date or date.min, found.voucher_no))


@dataclass(frozen=True, slots=True)
class Balance:
	currency: str
	invoiced: Decimal
	paid: Decimal
	outstanding: Decimal


def balances(found: Iterable[Item]) -> list[Balance]:
	"""The sums of each currency, in the order the currencies first appear; amounts of two currencies are never
	added up."""
	sums: dict[str, list[Decimal]] = {}
	for each in found:
		total = sums.setdefault(each.currency, [Decimal(0), Decimal(0), Decimal(0)])
		total[0] += each.invoiced
		total[1] += each.paid
		total[2] += each.outstanding
	return [Balance(currency, *amounts) for currency, amounts in sums.items()]


OURS = "ours"
YOURS = "yours"
BALANCED = "balanced"


def favour(party_type: str, outstanding: Decimal) -> str:
	"""Whose favour a balance is in: what a customer owes is in ours; the report Accounts Payable shows what is owed to
	a supplier as a positive amount, which is in the supplier's favour."""
	if not outstanding:
		return BALANCED
	owed_to_us = outstanding > 0 if party_type == "Customer" else outstanding < 0
	return OURS if owed_to_us else YOURS


STATEMENT_TEXT = "As of {0}, our books show the following open items on your account."
NO_ITEMS = "As of {0}, our books show no open items on your account."
BALANCE_TEXTS = {
	OURS: "As of {0}, the balance is {1} in our favour.",
	YOURS: "As of {0}, the balance is {1} in your favour.",
	BALANCED: "As of {0}, your account is balanced.",
}
STATES_NOTHING_TITLE = "This document states nothing:"
WRONG_KIND = "The print format does not match the kind of this document."
CANCELLED = "This document has been cancelled."


# The request for a balance confirmation asks the party to reply in any case, agreeing or naming a difference: a
# positive confirmation request in the terms of ISA 505.6(b) (docs/saldenbestaetigung.md).
def asks(kind: str, printed_kind: str, docstatus: int) -> bool:
	return printed_kind == BALANCE_CONFIRMATION and states(kind, printed_kind, docstatus) and docstatus == 1


REQUEST = "Please check this balance and return the confirmation below, signed."
REQUEST_BY = "Please check this balance and return the confirmation below, signed, by {0}."
REPLY_TO = "Please send it directly to the address named in the reply."


def request(has_deadline: bool) -> str:
	return REQUEST_BY if has_deadline else REQUEST


def beneficiary(party_type: str, outstanding: Decimal, company: str, party: str) -> str:
	"""Whom the balance favours, by name, for the reply that the party writes."""
	side = favour(party_type, outstanding)
	return {OURS: company, YOURS: party}.get(side, "")


CONFIRM = "We confirm the balance of {0} as of {1} in favour of {2}."
CONFIRM_BALANCED = "We confirm that the account is balanced as of {0}."
DIFFERENCE = "We find the following difference:"
OUR_BALANCE = "Our balance according to our books:"
REPLY_TITLE = "Confirmation of the balance"
REPLY_FIELDS = ("Place and date", "Signature", "Name and company stamp")


def confirmation(outstanding: Decimal) -> str:
	return CONFIRM if outstanding else CONFIRM_BALANCED
