"""The Kontoauszug or Saldenbestätigung of a customer or supplier as of a cut-off date (docs/kontoauszug.md). Its
rows are those of ERPNext's report Accounts Receivable or Accounts Payable for the party (briefbote/statement): a
draft reads them each time it is saved, and on submission the document keeps the rows it read, so that what went out
reprints as it was sent; a later posting dated before the cut-off date changes no submitted statement."""

from frappe.model.document import Document

from briefbote.briefbote import statement as ledger
from briefbote.statement import statement


class PartyStatement(Document):
	def before_naming(self):
		self.naming_series = statement.series(self.kind)

	def validate(self):
		self.party_name = ledger.party_name(self.party_type, self.party)
		if self._action in ("save", "submit"):
			self.read_ledger()

	def read_ledger(self):
		found = ledger.ledger_items(self.company, self.party_type, self.party, self.report_date)
		self.set("items", [ledger.item_row(each) for each in found])
		self.set("balances", [ledger.balance_row(each) for each in statement.balances(found)])
