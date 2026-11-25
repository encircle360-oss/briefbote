"""What an invoice or a Gutschrift lacks of the particulars the law asks of it, for the block a print format prints
at the top of a document that is incomplete.

§ 14 Abs. 4 Satz 1 UStG lists the particulars of an invoice: the full name and address of supplier and recipient
(Nr. 1), the Steuernummer or USt-IdNr. of the supplier (Nr. 2), the date of the supply (Nr. 6), the consideration by
tax rates (Nr. 7) and the rate and amount of the tax or a notice of the exemption (Nr. 8). A Gutschrift is the
invoice of the supplier (§ 14 Abs. 2 Satz 5 UStG): its Nr. 2 is the number of the supplier. § 14a Abs. 1 and 3 UStG
add the USt-IdNr. of both parties for a service and a supply within the EU. An invoice of at most 250 euros needs
none of these but the consideration and the tax (§ 33 UStDV); that relief does not apply to the cases of § 14a
(§ 33 Satz 3 UStDV). A commercial credit is no invoice and needs none of them. docs/rechnung.md lists the findings.
"""

from dataclasses import dataclass

HEADING = "This document is incomplete and must not be sent as an invoice:"
RECIPIENT_ADDRESS = "The full address of the recipient is missing (Section 14(4) sentence 1 no. 1 UStG)."
OWN_TAX_ID = "The tax number or VAT ID of the company is missing (Section 14(4) sentence 1 no. 2 UStG)."
SUPPLIER_TAX_ID = "The tax number or VAT ID of the supplier is missing (Section 14(4) sentence 1 no. 2 UStG)."
SERVICE_DATE = "The date of the supply or service is missing (Section 14(4) sentence 1 no. 6 UStG)."
RECIPIENT_VAT_ID = "The VAT ID of the recipient is missing (Section 14a(1) and (3) UStG)."
OWN_VAT_ID = "The VAT ID of the company is missing (Section 14a(1) and (3) UStG)."
NO_TAX = (
	"The supply is taxable in Germany, but the document charges no VAT and states no reason "
	"(Section 14(4) sentence 1 no. 8 UStG)."
)
TAX_BASE = (
	"The consideration of a tax rate cannot be determined from the tax details of the document "
	"(Section 14(4) sentence 1 no. 7 and 8 UStG)."
)
NOT_SELF_BILLING = "This Purchase Invoice is not marked as self-billing; the print format Gutschrift prints only a document marked so."
TEXTS = (
	HEADING,
	RECIPIENT_ADDRESS,
	OWN_TAX_ID,
	SUPPLIER_TAX_ID,
	SERVICE_DATE,
	RECIPIENT_VAT_ID,
	OWN_VAT_ID,
	NO_TAX,
	TAX_BASE,
	NOT_SELF_BILLING,
)
SMALL_AMOUNT = 250


@dataclass(frozen=True, slots=True)
class Facts:
	"""What a document holds. issuer_tax_id is the number of the supplier: of the company on an invoice, of the
	supplier on a Gutschrift."""

	self_billing: bool = False
	credit: bool = False
	small_amount: bool = False
	recipient_address: bool = True
	issuer_tax_id: bool = True
	service_date: bool = True
	needs_both_vat_ids: bool = False
	recipient_vat_id: bool = True
	own_vat_id: bool = True
	taxable: bool = False
	charges_tax: bool = True
	states_reason: bool = False
	bases_known: bool = True


def missing(facts: Facts) -> list[str]:
	"""The texts of the particulars the document lacks, in the order of § 14 Abs. 4 Satz 1 UStG."""
	if facts.credit:
		return []
	found = []
	relieved = facts.small_amount and not facts.needs_both_vat_ids
	if not relieved:
		if not facts.recipient_address:
			found.append(RECIPIENT_ADDRESS)
		if not facts.issuer_tax_id:
			found.append(SUPPLIER_TAX_ID if facts.self_billing else OWN_TAX_ID)
		if not facts.service_date:
			found.append(SERVICE_DATE)
	if facts.taxable and not facts.charges_tax and not facts.states_reason:
		found.append(NO_TAX)
	if not facts.bases_known:
		found.append(TAX_BASE)
	if facts.needs_both_vat_ids:
		if not facts.recipient_vat_id:
			found.append(RECIPIENT_VAT_ID)
		if not facts.own_vat_id:
			found.append(OWN_VAT_ID)
	return found
