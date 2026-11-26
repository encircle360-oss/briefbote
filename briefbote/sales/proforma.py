"""The Proforma-Rechnung: what ERPNext 16 prints from the copy of a Sales Order that a Proforma Invoice renders, a
statement of what an order will be invoiced at, for instance for customs or a prepayment. It is no invoice: it
settles no supply (§ 14 Abs. 1 Satz 1 UStG) and says so. docs/proforma-rechnung.md names each source.

Tax shown separately in a document with the issuer, the recipient, a description of the supply and the consideration
is owed by whoever issued it, even where the document is no proper invoice (§ 14c Abs. 2 UStG, UStAE 14c.2 Abs. 1
Satz 3 to 6); it is shown separately once it is named as an amount of money and marked as tax, also in an explaining
note (Satz 6 to 9). The proforma therefore names no tax amount and no rate, only the total with tax.
"""

from datetime import date

TITLE = "Proforma Invoice"
PROFORMA_NO = "Proforma No."
OUR_ORDER = "Our Order"
TOTAL = "Total Amount"
TOTAL_WITH_VAT = "Total Amount including VAT"
# § 15 Abs. 1 Satz 1 Nr. 1 UStG: input tax is deducted on an invoice under §§ 14, 14a UStG.
NOT_AN_INVOICE = (
	"This proforma invoice is not an invoice within the meaning of Section 14 UStG and does not entitle the "
	"recipient to deduct input tax (Section 15(1) sentence 1 no. 1 UStG)."
)
INVOICE_FOLLOWS = "You will receive the invoice separately."
TEXTS = (TITLE, PROFORMA_NO, OUR_ORDER, TOTAL, TOTAL_WITH_VAT, NOT_AN_INVOICE, INVOICE_FOLLOWS)


def closing(asks: bool) -> list[str]:
	"""That the proforma is no invoice, always, and the announcement of the invoice on a valid proforma only
	(briefbote/layout/status.py)."""
	return [NOT_AN_INVOICE, INVOICE_FOLLOWS] if asks else [NOT_AN_INVOICE]


def total_label(charges_tax: bool) -> str:
	return TOTAL_WITH_VAT if charges_tax else TOTAL


def reference(
	number: str, issued: date | None, order: str, ordered: date
) -> tuple[tuple[str, date | None] | None, tuple[str, date]]:
	"""The number and day of the proforma where ERPNext gave it one, and the order it is drawn from."""
	return ((number, issued) if number else None), (order, ordered)
