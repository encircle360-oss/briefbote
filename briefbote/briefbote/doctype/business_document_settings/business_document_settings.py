import frappe
from frappe import _
from frappe.model.document import Document

from briefbote.dunning import interest


def seed_base_rates(settings) -> None:
	"""The base rates the Bundesbank has published, for settings that have none; the company confirms each new one."""
	if not settings.get("base_rates"):
		for row in interest.PUBLISHED:
			settings.append("base_rates", {"valid_from": row.valid_from, "rate": row.rate})


class BusinessDocumentSettings(Document):
	def before_insert(self):
		seed_base_rates(self)

	def validate(self):
		self.validate_bank_accounts()
		self.validate_tax_cases()
		self.validate_dunning()

	def validate_dunning(self):
		for table, field in (("base_rates", "valid_from"), ("dunning_levels", "level")):
			seen = set()
			for row in self.get(table):
				if row.get(field) in seen:
					frappe.throw(_("Row {0}: {1} is there twice.").format(row.idx, row.get(field)))
				seen.add(row.get(field))

	def validate_bank_accounts(self):
		"""The footer and the payment request print only accounts of the company itself."""
		for row in self.bank_accounts:
			account = frappe.db.get_value(
				"Bank Account", row.bank_account, ["company", "is_company_account"], as_dict=True
			)
			if not account or not account.is_company_account or account.company != self.company:
				frappe.throw(
					_("Row {0}: {1} is no bank account of {2}.").format(
						row.idx, row.bank_account, self.company
					)
				)

	def validate_tax_cases(self):
		seen = set()
		for row in self.tax_cases:
			if row.taxes_and_charges in seen:
				frappe.throw(_("Row {0}: {1} has a tax case already.").format(row.idx, row.taxes_and_charges))
			seen.add(row.taxes_and_charges)
			company = frappe.db.get_value(
				"Sales Taxes and Charges Template", row.taxes_and_charges, "company"
			)
			if company != self.company:
				frappe.throw(
					_("Row {0}: {1} is no template of {2}.").format(
						row.idx, row.taxes_and_charges, self.company
					)
				)
