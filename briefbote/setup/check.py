"""What a company lacks for its printouts, for the whitelisted check of the Einstellungen Geschäftspost
(briefbote/briefbote/setup.py): the settings themselves, the particulars a business letter and an invoice must carry
(§ 14 Abs. 4 Satz 1 Nr. 1 and 2 UStG, § 35a GmbHG and its siblings, docs/geschaeftsbrief.md), a bank account for the
payment request, a logo, and the tax templates without a tax case.

An error makes printouts that lack a mandatory particular; a warning, printouts that lack what most companies need or
must state by their legal form, which the check cannot know; a note, something to look at.
"""

from dataclasses import dataclass

ERROR = "error"
WARNING = "warning"
INFO = "info"

NO_SETTINGS = (
	"{0} has no Einstellungen Geschäftspost; its printouts use the defaults and lack its particulars."
)
NO_ADDRESS = "The company has no address for the return address and the footer."
NO_TAX_ID = "The company has neither a VAT ID nor a tax number, one of which every invoice must state."
NO_REGISTERED_OFFICE = "The registered office is missing."
NO_REGISTER = "Register court and register number are missing."
NO_MANAGEMENT = "Neither managing directors nor an executive board are named."
NO_BANK = "No bank account is chosen; invoices ask for payment without one."
NO_LOGO = "No logo is chosen; the letterhead shows the name of the company."
UNMAPPED_SALES = "The sales tax template {0} has no tax case; its invoices print as taxable in Germany."
UNMAPPED_PURCHASE = (
	"The purchase tax template {0} has no tax case; its Gutschriften print as taxable in Germany."
)
TEXTS = (
	NO_SETTINGS,
	NO_ADDRESS,
	NO_TAX_ID,
	NO_REGISTERED_OFFICE,
	NO_REGISTER,
	NO_MANAGEMENT,
	NO_BANK,
	NO_LOGO,
	UNMAPPED_SALES,
	UNMAPPED_PURCHASE,
)


@dataclass(frozen=True, slots=True)
class Company:
	name: str
	has_settings: bool
	blank_paper: bool = True
	logo: bool = False
	address: bool = False
	registered_office: bool = False
	register: bool = False
	management: bool = False
	vat_id: bool = False
	tax_number: bool = False
	bank_accounts: int = 0
	unmapped_sales: tuple[str, ...] = ()
	unmapped_purchase: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Finding:
	level: str
	text: str
	values: tuple[str, ...]


def findings(company: Company) -> list[Finding]:
	if not company.has_settings:
		return [Finding(ERROR, NO_SETTINGS, (company.name,))]
	found = []
	if not company.address:
		found.append(Finding(ERROR, NO_ADDRESS, ()))
	if not (company.vat_id or company.tax_number):
		found.append(Finding(ERROR, NO_TAX_ID, ()))
	if company.blank_paper:
		if not company.registered_office:
			found.append(Finding(WARNING, NO_REGISTERED_OFFICE, ()))
		if not company.register:
			found.append(Finding(WARNING, NO_REGISTER, ()))
		if not company.management:
			found.append(Finding(WARNING, NO_MANAGEMENT, ()))
	if not company.bank_accounts:
		found.append(Finding(WARNING, NO_BANK, ()))
	if company.blank_paper and not company.logo:
		found.append(Finding(INFO, NO_LOGO, ()))
	found += [Finding(WARNING, UNMAPPED_SALES, (name,)) for name in company.unmapped_sales]
	found += [Finding(INFO, UNMAPPED_PURCHASE, (name,)) for name in company.unmapped_purchase]
	return found
