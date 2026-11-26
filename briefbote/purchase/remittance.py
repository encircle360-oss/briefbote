"""The Zahlungsavis of a Payment Entry: the advice to a supplier that a payment was made and which of its invoices it
settles, by the supplier's own invoice numbers, with the cash discount taken. It is the mirror of the
Zahlungsbestätigung (briefbote/sales/receipt.py). No law prescribes it; it is a business letter (§ 35a GmbHG) and
announces only a payment that was booked. docs/zahlungsavis.md names the sources.
"""

from collections.abc import Iterable
from decimal import Decimal

TITLE = "Remittance Advice"


def advises(payment_type: str, party_type: str, docstatus: int) -> bool:
	return payment_type == "Pay" and party_type == "Supplier" and docstatus == 1


TRANSFERRED = "On {0} we transferred the amount of {1}, applied as follows."
PAID = "On {0} we paid the amount of {1}, applied as follows."
TRANSFERRED_TOTAL = "Transferred"
PAID_TOTAL = "Paid"
# The type of a Mode of Payment in ERPNext whose payments go through a bank account.
BANK = "Bank"


def text(mode_type: str) -> str:
	"""Transferred where the mode of payment is one through a bank, paid otherwise: cash, cheque or a mode the
	desk gives no type."""
	return TRANSFERRED if mode_type == BANK else PAID


def total_label(mode_type: str) -> str:
	return TRANSFERRED_TOTAL if mode_type == BANK else PAID_TOTAL


SETTLED = "Settled"
NOT_APPLIED = "Not applied to an invoice"
NOT_ADVISED = "Only a submitted payment to a supplier is advised; this document announces no payment."
NO_PAYMENT_TITLE = "This document announces no payment:"
INCOMPLETE_TITLE = "This remittance advice is incomplete:"
NO_BILL_NUMBER = "Invoice {0} carries no invoice number of the supplier."


def shows_discount(discounts: Iterable[Decimal]) -> bool:
	return any(discount for discount in discounts)


def without_bill_number(rows: Iterable[tuple[str, str, str]]) -> list[str]:
	"""Our numbers of the purchase invoices among (doctype, name, bill_no) that lack the supplier's number."""
	return [name for doctype, name, bill_no in rows if doctype == "Purchase Invoice" and not bill_no]


def _compact(iban: str) -> str:
	return "".join(iban.split()).upper()


def own_account(iban: str, shown: Iterable[str]) -> str:
	"""The IBAN the payment came from, where the foot of the letter shows it anyway; else nothing."""
	number = _compact(iban)
	return number if number and number in {_compact(other) for other in shown} else ""
