"""The tax case of a tax template by its title, for setting up the Einstellungen Geschäftspost without the desk.

The rule knows the titles the setup of ERPNext 16 gives the sales and purchase tax templates of a company in Germany
(erpnext/setup/setup_wizard/data/country_wise_tax.json, the same for SKR03, SKR04 and the standard chart). A template
it does not know gets no case; the check of the settings names it, and a person decides.

Not known on purpose: „Nullsteuersatz nach § 12 Abs. 3 UStG“, a taxable supply at a rate of 0 %, which needs the rate
printed and no notice of an exemption; and purchases from suppliers abroad, whose Gutschrift follows the rules of the
supplier's state (Art. 219a of the VAT Directive).
"""

from briefbote.invoice.document import Case
from briefbote.invoice.self_billing import PurchaseCase

SALES = {
	"Lieferung oder sonstige Leistung im Inland": Case.DOMESTIC,
	"Lieferung an Unternehmen in der EU": Case.INTRA_COMMUNITY_SUPPLY,
	"Sonstige Leistung an Unternehmen in der EU": Case.EU_SERVICE,
	"Lieferung oder sonstige Leistung an nicht-Unternehmen in der EU": Case.DOMESTIC,
	"Lieferung in Drittland": Case.EXPORT,
	"Sonstige Leistung an Unternehmen in Drittland": Case.NON_EU_SERVICE,
	"Sonstige Leistung an nicht-Unternehmen in Drittland": Case.DOMESTIC,
	"Bauleistungen nach § 13b UStG": Case.REVERSE_CHARGE,
}
PURCHASE = {
	"Lieferung aus dem Inland": PurchaseCase.DOMESTIC,
	"Sonstige Leistung aus dem Inland": PurchaseCase.DOMESTIC,
	"Bauleistungen nach § 13b UStG": PurchaseCase.REVERSE_CHARGE,
}


def title(name: str, abbreviation: str) -> str:
	"""The title of a template from its name, which ERPNext makes of the title and the abbreviation of the company."""
	return name.removesuffix(f" - {abbreviation}")


def sales_case(template_title: str) -> Case | None:
	return SALES.get(template_title)


def purchase_case(template_title: str) -> PurchaseCase | None:
	return PURCHASE.get(template_title)
