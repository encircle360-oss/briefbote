"""What an outgoing invoice says beyond its positions: which kind of document it is, which notices its tax case needs
and when the service was rendered. The texts are the English source; the print format gives them in the language of
the document (briefbote/translations/de.csv). docs/rechnung.md names each source and what it says.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum


class Kind(StrEnum):
	"""The kinds of document a Sales Invoice prints as.

	A return against an invoice corrects that invoice by a document that refers to it specifically and unambiguously
	(§ 31 Abs. 5 UStDV, UStAE 14.11 Abs. 1): a cancellation where it reverses the whole invoice, a correction
	otherwise. A return without an invoice is a commercial credit, such as a bonus or a goodwill reduction of the
	price. None of them is a Gutschrift in the sense of § 14 Abs. 2 Satz 5 UStG, which only the recipient of a supply
	issues (UStAE 14.3 Abs. 2 Satz 5), so none is titled with that word alone.
	"""

	INVOICE = "invoice"
	CANCELLATION = "cancellation"
	CORRECTION = "correction"
	CREDIT = "credit"


TITLES = {
	Kind.INVOICE: "Invoice",
	Kind.CANCELLATION: "Cancellation Invoice",
	Kind.CORRECTION: "Invoice Correction",
	Kind.CREDIT: "Commercial Credit Note",
}

# Amounts that differ by less than this are the same, as the rounding of ERPNext leaves them.
CENT = Decimal("0.005")


def kind_of(
	is_return: bool, return_against: str, grand_total: Decimal, original_total: Decimal | None
) -> Kind:
	if not is_return:
		return Kind.INVOICE
	if not return_against:
		return Kind.CREDIT
	if original_total is not None and abs(original_total + grand_total) < CENT:
		return Kind.CANCELLATION
	return Kind.CORRECTION


class Case(StrEnum):
	"""The tax case of an invoice, which the Einstellungen Geschäftspost give each sales tax template."""

	DOMESTIC = "Taxable in Germany"
	INTRA_COMMUNITY_SUPPLY = "Intra-Community supply"
	EU_SERVICE = "Service to a business in another EU country"
	REVERSE_CHARGE = "Reverse charge in Germany"
	EXPORT = "Export"
	NON_EU_SERVICE = "Service to a business outside the EU"
	EXEMPT = "Tax exempt"


def case(name: str | None) -> Case:
	return Case(name) if name else Case.DOMESTIC


# § 4 Nr. 1 Buchst. b, § 6a UStG; the notice of § 14 Abs. 4 Satz 1 Nr. 8 UStG, UStAE 14a.1 Abs. 4.
INTRA_COMMUNITY_SUPPLY = (
	"Tax-exempt intra-Community supply (Section 4 No. 1(b) in conjunction with Section 6a UStG)."
)
# § 14a Abs. 1 UStG: „Steuerschuldnerschaft des Leistungsempfängers“, or „Reverse charge“ of Art. 226 Nr. 11a of the
# VAT Directive (UStAE 14a.1 Abs. 2 Satz 3, Abs. 6 Satz 2).
EU_SERVICE = "Reverse charge: the recipient of the service is liable for the tax. The service is not taxable in Germany (Section 3a(2) UStG)."
# § 13b Abs. 2, 5, § 14a Abs. 5 UStG; without the notice the recipient still owes the tax, a tax shown is owed by the
# supplier under § 14c Abs. 1 UStG (UStAE 13b.14 Abs. 1).
REVERSE_CHARGE = "Reverse charge: the recipient of the service is liable for the tax (Section 13b UStG)."
# § 4 Nr. 1 Buchst. a, § 6 UStG; the notice of § 14 Abs. 4 Satz 1 Nr. 8 UStG, UStAE 14.5 Abs. 20.
EXPORT = "Tax-exempt export delivery (Section 4 No. 1(a) in conjunction with Section 6 UStG)."
# No law asks for a notice where the place of the service lies outside the EU (UStAE 14.1 Abs. 20); the notice says
# why the invoice shows no tax, and calls the service not taxable, never tax-exempt.
NON_EU_SERVICE = "Not taxable in Germany: the place of the service lies outside the EU (Section 3a(2) UStG)."
# § 14 Abs. 4 Satz 1 Nr. 8 UStG: a notice that an exemption applies; its reason in plain words (UStAE 14.5 Abs. 20).
EXEMPT = "Tax-exempt supply: {0}"
# § 19 Abs. 1 UStG, § 34a Satz 1 Nr. 5 UStDV, UStAE 14.7a Abs. 1.
SMALL_BUSINESS = "No VAT is charged: tax exemption for small businesses under Section 19 UStG."
# UStAE 14c.1 Abs. 3 Satz 4: the word alone does not make a commercial credit a Gutschrift of § 14 Abs. 2 Satz 5 UStG;
# the notice says what it is.
COMMERCIAL_CREDIT = "This credit note reduces the consideration for earlier supplies or services (Section 17 UStG). It is not a self-billing invoice under Section 14(2) sentence 5 UStG."

_CASE_NOTICES = {
	Case.INTRA_COMMUNITY_SUPPLY: INTRA_COMMUNITY_SUPPLY,
	Case.EU_SERVICE: EU_SERVICE,
	Case.REVERSE_CHARGE: REVERSE_CHARGE,
	Case.EXPORT: EXPORT,
	Case.NON_EU_SERVICE: NON_EU_SERVICE,
}


def needs_both_vat_ids(tax_case: Case, small_business: bool) -> bool:
	"""§ 14a Abs. 1 Satz 3 and Abs. 3 Satz 2 UStG; § 19 Abs. 1 Satz 2 UStG lifts both for a small business."""
	return not small_business and tax_case in {Case.INTRA_COMMUNITY_SUPPLY, Case.EU_SERVICE}


def charges_tax(tax_case: Case, small_business: bool) -> bool:
	return not small_business and tax_case is Case.DOMESTIC


type Notice = tuple[str, tuple[str, ...]]


def notices(
	kind: Kind, tax_case: Case, small_business: bool = False, exemption_reason: str = ""
) -> list[Notice]:
	"""The notices of the invoice, each a text with the values it names."""
	found: list[Notice] = [(COMMERCIAL_CREDIT, ())] if kind is Kind.CREDIT else []
	if small_business:
		return [*found, (SMALL_BUSINESS, ())]
	if tax_case is Case.EXEMPT:
		return [*found, (EXEMPT, (exemption_reason,))] if exemption_reason else found
	if tax_case in _CASE_NOTICES:
		found.append((_CASE_NOTICES[tax_case], ()))
	return found


SERVICE_PERIOD = "Service Period"
SERVICE_DATE = "Service Date"
DELIVERY_DATE = "Delivery Date"
DELIVERY_PERIOD = "Delivery Period"


def service(
	posting_date: date,
	from_date: date | None = None,
	to_date: date | None = None,
	item_periods: list[tuple[date | None, date | None]] | tuple = (),
	delivery_dates: list[date] | tuple = (),
) -> tuple[str, tuple[date, ...]]:
	"""The time of the supply or service (§ 14 Abs. 4 Satz 1 Nr. 6 UStG), always as a date or a period: the period
	of the invoice, else the span of the periods of its items, else the day or days of its deliveries, else the day of
	the invoice. UStAE 14.5 Abs. 16 asks for the date even where it is the day of the invoice."""
	if from_date and to_date:
		return SERVICE_PERIOD, (from_date, to_date)
	periods = [(start, end) for start, end in item_periods if start and end]
	if periods:
		return SERVICE_PERIOD, (min(start for start, _ in periods), max(end for _, end in periods))
	days = sorted(set(delivery_dates))
	if len(days) == 1:
		return DELIVERY_DATE, (days[0],)
	if days:
		return DELIVERY_PERIOD, (days[0], days[-1])
	return SERVICE_DATE, (posting_date,)


# § 286 Abs. 3 Satz 1 BGB: a debtor of a payment defaults 30 days after the due date and the receipt of the invoice,
# a consumer only where the invoice points this out.
CONSUMER_DEFAULT = "If you do not pay within 30 days of the due date and receipt of this invoice, you will be in default without a reminder (Section 286(3) BGB)."
