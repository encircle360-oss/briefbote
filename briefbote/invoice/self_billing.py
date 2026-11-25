"""The self-billing invoice, Gutschrift: the recipient of a supply settles it with the supplier by a document it issues
itself, as agreed beforehand (§ 14 Abs. 2 Satz 5 UStG). It is an invoice of the supplier: it carries the word
„Gutschrift“ (§ 14 Abs. 4 Satz 1 Nr. 10 UStG) and the Steuernummer or USt-IdNr. of the supplier (Nr. 2), the
supplier's tax as Umsatzsteuer, and the notices of the supplier's tax case. docs/gutschrift.md names the sources.

The cases are those of a supplier in Germany; a supplier in another member state invoices by the rules of its own
state (Art. 219a of the VAT Directive), which Briefbote does not print yet.
"""

from enum import StrEnum

from briefbote.invoice import document
from briefbote.invoice.document import Kind

TITLES = {
	Kind.INVOICE: "Self-Billing Invoice",
	Kind.CORRECTION: "Correction of the Self-Billing Invoice",
	Kind.CANCELLATION: "Cancellation of the Self-Billing Invoice",
	Kind.CREDIT: "Correction of the Self-Billing Invoice",
}

# § 14 Abs. 2 Satz 5 UStG.
SELF_BILLING = "Settled by the recipient of the supply by self-billing (Section 14(2) sentence 5 UStG)."


class PurchaseCase(StrEnum):
	"""The tax case of the supply the Gutschrift settles, which the Einstellungen Geschäftspost give each purchase tax
	template."""

	DOMESTIC = "Taxable in Germany"
	REVERSE_CHARGE = "Reverse charge in Germany"
	SMALL_BUSINESS = "Supplier is a small business"
	EXEMPT = "Tax exempt"


def case(name: str | None) -> PurchaseCase:
	return PurchaseCase(name) if name else PurchaseCase.DOMESTIC


def charges_tax(tax_case: PurchaseCase) -> bool:
	return tax_case is PurchaseCase.DOMESTIC


def notices(tax_case: PurchaseCase, exemption_reason: str = "") -> list[document.Notice]:
	found: list[document.Notice] = [(SELF_BILLING, ())]
	if tax_case is PurchaseCase.REVERSE_CHARGE:
		found.append((document.REVERSE_CHARGE, ()))
	elif tax_case is PurchaseCase.SMALL_BUSINESS:
		found.append((document.SMALL_BUSINESS, ()))
	elif tax_case is PurchaseCase.EXEMPT and exemption_reason:
		found.append((document.EXEMPT, (exemption_reason,)))
	return found
