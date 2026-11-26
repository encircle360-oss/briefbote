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
LOGO_UNREADABLE = "The logo cannot be read or has no size of its own; upload it as PNG, JPEG or SVG with a viewBox or width and height."
RETURN_ADDRESS_TOO_LONG = (
	"Name and address of the company do not fit the return address above the address field even in two lines at 6 pt; "
	"shorten the street or switch the return address off."
)
FOOT_TOO_LONG = (
	"The block “{0}” of the footer needs {1} lines in {2} printouts instead of four; its last line runs into the gap "
	"above the page line. Shorten the bank name, the register court or the names of the management."
)
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
	LOGO_UNREADABLE,
	RETURN_ADDRESS_TOO_LONG,
	FOOT_TOO_LONG,
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
	logo_readable: bool = True
	return_address_fits: bool = True
	# Each block of the footer that needs more than four lines: its name, its lines and the language of the printouts.
	foot_overflows: tuple[tuple[str, str, str], ...] = ()


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
	if company.blank_paper and company.logo and not company.logo_readable:
		found.append(Finding(WARNING, LOGO_UNREADABLE, ()))
	if not company.return_address_fits:
		found.append(Finding(WARNING, RETURN_ADDRESS_TOO_LONG, ()))
	if company.blank_paper:
		found += [Finding(WARNING, FOOT_TOO_LONG, overflow) for overflow in company.foot_overflows]
	found += [Finding(WARNING, UNMAPPED_SALES, (name,)) for name in company.unmapped_sales]
	found += [Finding(INFO, UNMAPPED_PURCHASE, (name,)) for name in company.unmapped_purchase]
	return found
