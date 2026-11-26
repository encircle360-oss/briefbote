"""The payments a final invoice deducts: which of them are advances in the sense of § 14 Abs. 5 UStG, what of their
consideration and tax is known, and what remains to pay. docs/rechnung.md names each source.

§ 14 Abs. 5 Satz 2 UStG: a final invoice (Endrechnung) deducts the Teilentgelte received before the supply and the
tax on them, where invoices were issued for them. UStAE 14.8 Abs. 7 Satz 3 allows the gross amounts of the advances to
be deducted with the tax they contain stated beside them, Satz 4 lets the invoice leave out the tax on the remainder
where it states the tax of the whole supply. Abs. 10: a final invoice that does not deduct them owes the tax shown on
the advances once more under § 14c Abs. 1 UStG.

ERPNext 16 books an advance as a Payment Entry. Its tax stands in the table taxes (Advance Taxes and Charges); a line
„On Paid Amount“ included in the paid amount takes the tax out of the payment, and the Payment Entry credits the
customer the rest (get_base_unallocated_amount and get_included_taxes in
erpnext/accounts/doctype/payment_entry/payment_entry.py). An invoice that allocates the advance in its table advances
(Sales Invoice Advance) therefore allocates the consideration without the tax. Any other advance, such as a Journal
Entry, carries no tax; Briefbote derives none for it.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
# Amounts that differ by less than this are the same, as the rounding of ERPNext leaves them.
SAME = Decimal("0.005")

FINAL_INVOICE = "Final Invoice"
HEADING = "Less the advance payments received before the supply (Section 14(5) sentence 2 UStG):"
ADVANCE = "Advance payment of {0}, payment {1}"
ADVANCE_INVOICED = "Advance payment of {0}, payment {1}, advance invoice {2} of {3}"
CONSIDERATION = "Consideration"
RATE = "Rate"
VAT_AMOUNT = "VAT"
GROSS = "Amount"
SUM = "Total of the advance payments"
LATER = "Less payments received"
REMAINDER = "Remaining Amount"
UNKNOWN = "\u2013"
UNSPLIT = (
	"The advance payment {0} shows no VAT. If an invoice with VAT was issued for it, the final invoice must deduct "
	"the VAT on it (Section 14(5) sentence 2 UStG); book the advance with its VAT in the payment entry."
)
TEXTS = (
	FINAL_INVOICE,
	HEADING,
	ADVANCE,
	ADVANCE_INVOICED,
	CONSIDERATION,
	RATE,
	VAT_AMOUNT,
	GROSS,
	SUM,
	LATER,
	REMAINDER,
	UNSPLIT,
)


@dataclass(frozen=True, slots=True)
class Tax:
	"""A tax line of a payment entry: its rate and amount, whether it is reckoned on the paid amount, included in it
	and added rather than deducted."""

	rate: Decimal
	amount: Decimal
	on_paid_amount: bool = True
	included: bool = True
	added: bool = True


@dataclass(frozen=True, slots=True)
class Payment:
	"""A payment the invoice allocates: its document, the day it was received, the amount allocated to the invoice,
	the amount the payment credits the customer, its tax lines and the advance invoice that billed it, if known."""

	name: str
	received: date
	allocated: Decimal
	credited: Decimal
	taxes: tuple[Tax, ...] = ()
	invoice: tuple[str, date] | None = None


@dataclass(frozen=True, slots=True)
class Deduction:
	payment: Payment
	gross: Decimal
	net: Decimal | None
	rate: Decimal | None
	tax: Decimal | None

	@property
	def known(self) -> bool:
		return self.net is not None and self.tax is not None


def _cent(value: Decimal) -> Decimal:
	return value.quantize(CENT, ROUND_HALF_UP)


def split(payment: Payment) -> Deduction:
	"""The consideration, rate and tax of the allocated part of an advance, where its payment entry has exactly one
	tax line, reckoned on the paid amount and included in it: the allocated amount is then the consideration, and the
	tax its share of the tax of the payment. Otherwise only the amount allocated is known."""
	lines = [tax for tax in payment.taxes if tax.amount]
	if len(lines) == 1 and payment.credited:
		line = lines[0]
		if line.on_paid_amount and line.included and line.added and line.rate:
			tax = _cent(line.amount * payment.allocated / payment.credited)
			return Deduction(payment, payment.allocated + tax, payment.allocated, line.rate, tax)
	return Deduction(payment, payment.allocated, None, None, None)


def is_advance(received: date, supplied: date) -> bool:
	"""Whether a payment was received before the supply was rendered, the last day of its date or period."""
	return received < supplied


@dataclass(frozen=True, slots=True)
class Settlement:
	advances: list[Deduction]
	later: Decimal
	remainder: Decimal
	unsplit: list[str]

	@property
	def final(self) -> bool:
		return bool(self.advances)

	@property
	def title(self) -> str:
		return FINAL_INVOICE if self.final else ""

	@property
	def gross(self) -> Decimal:
		return sum((deduction.gross for deduction in self.advances), Decimal(0))

	@property
	def net(self) -> Decimal | None:
		if not all(deduction.known for deduction in self.advances):
			return None
		return sum((deduction.net for deduction in self.advances), Decimal(0))

	@property
	def tax(self) -> Decimal | None:
		if not all(deduction.known for deduction in self.advances):
			return None
		return sum((deduction.tax for deduction in self.advances), Decimal(0))


def settle(total: Decimal, payments: Iterable[Payment], supplied: date, charges_tax: bool) -> Settlement:
	"""The advances before the supply with what is known of them, the payments after it, and the remainder of the
	total. On an invoice without VAT an advance carries none: its amount is its consideration."""
	found, later, unsplit = [], Decimal(0), []
	for payment in payments:
		if not is_advance(payment.received, supplied):
			later += payment.allocated
			continue
		deduction = split(payment)
		if not deduction.known:
			if charges_tax:
				unsplit.append(payment.name)
			else:
				deduction = Deduction(payment, payment.allocated, payment.allocated, None, Decimal(0))
		found.append(deduction)
	remainder = total - sum((deduction.gross for deduction in found), Decimal(0)) - later
	return Settlement(found, later, remainder, unsplit)


def label(payment: Payment) -> tuple[str, tuple]:
	"""The text of an advance in the deduction, with the advance invoice where it is known."""
	if payment.invoice:
		return ADVANCE_INVOICED, (payment.received, payment.name, *payment.invoice)
	return ADVANCE, (payment.received, payment.name)


def match(amount: Decimal, candidates: Iterable[tuple[str, date, Decimal]]) -> tuple[str, date] | None:
	"""The advance invoice of a payment: the only one of the same order with the amount the payment received.
	ERPNext keeps no link between the two, so two of that amount, or none, name none."""
	found = [(name, day) for name, day, total in candidates if abs(total - amount) < SAME]
	return found[0] if len(found) == 1 else None
