"""Setting up Briefbote without the desk: what a company lacks for its printouts, and the tax cases of its templates by
the rule of briefbote/setup/tax_cases.py. Both are whitelisted for scripts that provision a site through the REST API;
docs/einrichtung.md shows the calls.
"""

from decimal import Decimal

import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_default_address
from frappe.translate import print_language
from frappe.utils import cint, formatdate, getdate, nowdate

from briefbote.briefbote import printing
from briefbote.dunning import interest
from briefbote.layout import letter
from briefbote.setup import check as checks
from briefbote.setup import tax_cases

SETTINGS = printing.SETTINGS
# Who may read what a company lacks and set its tax cases: the roles that may change the settings.
ROLES = ("Accounts Manager", "System Manager")


def _allow() -> None:
	if not set(ROLES) & set(frappe.get_roles()):
		frappe.throw(
			_("Only an Accounts Manager or a System Manager may set up Briefbote."), frappe.PermissionError
		)


# The languages a document prints in, with their names for the check.
PRINT_LANGUAGES = {"de": "German", "en": "English"}


def _foot_overflows(particulars: letter.Company) -> tuple[tuple[str, str, str], ...]:
	"""Each block of the footer that needs more than four lines, in each language of the printouts, in the words of
	the user."""
	found = []
	for language, label in PRINT_LANGUAGES.items():
		with print_language(language):
			overflows = letter.foot_overflows(particulars, printing.t)
		found += [
			(_(name, context=printing.CONTEXT), str(lines), _(label, context=printing.CONTEXT))
			for name, lines in overflows
		]
	return tuple(found)


def _templates(doctype: str, company: str) -> list[str]:
	return frappe.get_all(doctype, filters={"company": company, "disabled": 0}, pluck="name", order_by="name")


def _company(company: str) -> checks.Company:
	if not frappe.db.exists(SETTINGS, company):
		return checks.Company(name=company, has_settings=False)
	config = frappe.get_doc(SETTINGS, company)
	tax_id = frappe.db.get_value("Company", company, "tax_id")
	mapped_sales = {row.taxes_and_charges for row in config.tax_cases}
	mapped_purchase = {row.purchase_taxes_and_charges for row in config.purchase_tax_cases}
	particulars = printing.company_particulars(company, config)
	return checks.Company(
		name=company,
		has_settings=True,
		blank_paper=config.stationery == printing.BLANK_PAPER,
		logo=bool(config.logo),
		address=bool(config.company_address or get_default_address("Company", company)),
		registered_office=bool(config.registered_office),
		register=bool(particulars.register_court and particulars.register_number),
		management=bool(particulars.managing_directors or particulars.executive_board),
		vat_id=bool(tax_id),
		tax_number=bool(config.tax_number),
		bank_accounts=len(config.bank_accounts),
		logo_readable=not config.logo or bool(printing.logo_proportions(config.logo)),
		return_address_fits=not config.print_return_address or letter.return_address(particulars).fits,
		foot_overflows=_foot_overflows(particulars),
		advance_invoices=bool(cint(frappe.db.get_single_value("Selling Settings", "enable_proforma_invoice")))
		and bool(frappe.db.exists("Print Format", {"name": printing.ADVANCE_FORMAT, "disabled": 0})),
		unmapped_sales=tuple(
			name
			for name in _templates("Sales Taxes and Charges Template", company)
			if name not in mapped_sales
		),
		unmapped_purchase=tuple(
			name
			for name in _templates("Purchase Taxes and Charges Template", company)
			if name not in mapped_purchase
		),
	)


@frappe.whitelist()
def check(company: str) -> list[dict]:
	"""What the company lacks for its printouts: a list of level and message, in the language of the user."""
	_allow()
	return [
		{"level": finding.level, "message": _(finding.text).format(*finding.values)}
		for finding in checks.findings(_company(company))
	] + _base_rate(company)


def _base_rate(company: str) -> list[dict]:
	"""A warning where the settings hold no base rate for today, so that dunning letters can check their interest
	(briefbote/dunning/interest.py)."""
	if not frappe.db.exists(SETTINGS, company):
		return []
	rates = [
		interest.BaseRate(getdate(row.valid_from), Decimal(str(row.rate)))
		for row in frappe.get_doc(SETTINGS, company).get("base_rates") or ()
	]
	today = getdate(nowdate())
	if interest.covers(rates, today, today):
		return []
	return [{"level": checks.WARNING, "message": _(interest.NO_BASE_RATE_TODAY).format(formatdate(today))}]


@frappe.whitelist()
def apply_tax_cases(company: str) -> dict:
	"""Give each tax template of the company that has no tax case the case the rule knows for its title; leave the
	others and every row that is there. Creates the settings where the company has none."""
	_allow()
	abbreviation = frappe.db.get_value("Company", company, "abbr")
	config = (
		frappe.get_doc(SETTINGS, company)
		if frappe.db.exists(SETTINGS, company)
		else frappe.new_doc(SETTINGS, company=company)
	)
	added = {"sales": [], "purchase": []}
	mapped = {row.taxes_and_charges for row in config.tax_cases}
	for name in _templates("Sales Taxes and Charges Template", company):
		case = tax_cases.sales_case(tax_cases.title(name, abbreviation))
		if name not in mapped and case:
			config.append("tax_cases", {"taxes_and_charges": name, "tax_case": case.value})
			added["sales"].append(name)
	mapped = {row.purchase_taxes_and_charges for row in config.purchase_tax_cases}
	for name in _templates("Purchase Taxes and Charges Template", company):
		case = tax_cases.purchase_case(tax_cases.title(name, abbreviation))
		if name not in mapped and case:
			config.append("purchase_tax_cases", {"purchase_taxes_and_charges": name, "tax_case": case.value})
			added["purchase"].append(name)
	config.save()
	return added
