"""Setting up Briefbote without the desk: what a company lacks for its printouts, and the tax cases of its templates by
the rule of briefbote/setup/tax_cases.py. Both are whitelisted for scripts that provision a site through the REST API;
docs/einrichtung.md shows the calls.
"""

import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_default_address

from briefbote.briefbote import printing
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
	]


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
