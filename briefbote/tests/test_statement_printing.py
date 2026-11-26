"""The Party Statement and its print format Kontoauszug on a site, for the ledger and statements of
print_documents_statement.py: the open items are those ERPNext's receivables and payables reports return, a submitted
statement keeps them, a draft reads the ledger anew, and a cancelled statement or one of the other kind states
nothing."""

from datetime import date
from decimal import Decimal

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import print_language

from briefbote.briefbote import statement as ledger
from briefbote.tests import print_documents as documents
from briefbote.tests import print_documents_dunning as dunning_documents
from briefbote.tests import print_documents_payment as payment_documents
from briefbote.tests import print_documents_remittance as remittance_documents
from briefbote.tests import print_documents_statement as statement_documents
from briefbote.tests.print_proof import FETCHED, LINK, SCRIPT

INLAND = documents.CUSTOMERS["inland"].name
OPEN_UNTIL_27 = [f"RE-2026-{300 + index:04d}" for index in range(1, 41)]


class StatementPrintingTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		documents.run()
		dunning_documents.run()
		payment_documents.run()
		remittance_documents.run()
		statement_documents.run()

	def statement(self, name: str, kind: str = "Open Items", language: str = "de", docstatus=None) -> dict:
		doc = frappe.get_doc("Party Statement", name)
		if docstatus is not None:
			doc.docstatus = docstatus
		with print_language(language):
			return ledger.briefbote_statement(doc, kind)

	def test_the_receivables_report_returns_what_the_ledger_of_the_proof_books(self):
		"""The numbers of a statement are those of ERPNext's own report, never a calculation of Briefbote."""
		rows = ledger.report_rows(documents.COMPANY, "Customer", INLAND, date(2026, 11, 26))
		found = {row["voucher_no"]: Decimal(str(row["outstanding"])) for row in rows}
		self.assertEqual(
			set(found),
			{"RE-2026-0201", "RE-2026-0202", "ZE-2026-0001", *OPEN_UNTIL_27},
			"RE-2026-0203 is paid",
		)
		self.assertEqual(found["RE-2026-0202"], Decimal(500))
		self.assertEqual(found["ZE-2026-0001"], Decimal(-25))

	def test_a_payment_after_the_cut_off_date_is_not_on_the_statement(self):
		rows = ledger.report_rows(documents.COMPANY, "Customer", INLAND, date(2026, 11, 27))
		self.assertFalse({row["voucher_no"] for row in rows} & set(OPEN_UNTIL_27))

	def test_the_submitted_statement_keeps_its_rows_and_balance(self):
		doc = frappe.get_doc("Party Statement", "KA-2026-0001")
		self.assertEqual(doc.docstatus, 1)
		self.assertEqual(len(doc.items), 43)
		self.assertEqual([(row.currency, row.outstanding) for row in doc.balances], [("EUR", 13565.0)])
		found = self.statement("KA-2026-0001")
		self.assertEqual(found["title"], "Kontoauszug")
		self.assertEqual(found["subject"], "Offene Posten zum 26.11.2026")
		self.assertEqual(found["totals"], [("Saldo", "13.565,00 €", "total")])
		self.assertEqual(found["closing"], ["Zum 26.11.2026 beträgt der Saldo 13.565,00 € zu unseren Gunsten."])
		self.assertEqual(
			found["text"],
			"Zum 26.11.2026 weisen unsere Bücher für Ihr Konto die folgenden offenen Posten aus.",
		)
		self.assertEqual(found["rows"][0]["name"], "RE-2026-0201")

	def test_a_booking_dated_before_the_cut_off_changes_a_draft_and_no_submitted_statement(self):
		"""A statement that went out reprints as it was sent; a draft shows the ledger as it is now."""
		_name, _day, invoice, amount = statement_documents.LATE
		submitted = {row["name"]: row for row in self.statement("KA-2026-0005")["rows"]}
		draft = {row["name"]: row for row in self.statement(statement_documents.LATER.name)["rows"]}
		self.assertEqual(submitted[invoice]["outstanding"], "1.190,00 €")
		self.assertEqual(draft[invoice]["outstanding"], "1.000,00 €")
		self.assertEqual(amount, Decimal(190))
		self.assertEqual(
			frappe.db.get_value("Party Statement", statement_documents.LATER.name, "docstatus"), 0
		)

	def test_a_supplier_statement_names_its_invoices_by_the_supplier_s_numbers(self):
		found = self.statement("KA-2026-0004")
		self.assertIn("Ihre Rechnung", [column["label"] for column in found["columns"]])
		self.assertEqual([row["reference"] for row in found["rows"]], ["RG-2026-1187", "RG-2026-1203"])
		self.assertEqual(found["closing"], ["Zum 26.11.2026 beträgt der Saldo 2.975,00 € zu Ihren Gunsten."])

	def test_an_account_without_open_items_says_so(self):
		found = self.statement("KA-2026-0003")
		self.assertEqual(
			(found["text"], found["rows"], found["totals"], found["closing"]),
			("Zum 30.11.2026 weisen unsere Bücher für Ihr Konto keine offenen Posten aus.", [], [], []),
		)

	def test_a_cancelled_statement_states_nothing(self):
		found = self.statement("KA-2026-0001", docstatus=2)
		self.assertEqual(found["findings"], ["Dieses Dokument ist storniert."])
		self.assertEqual((found["text"], found["closing"]), ("", []))
		self.assertEqual(len(found["rows"]), 43)

	def test_the_print_format_of_the_other_kind_states_nothing(self):
		found = self.statement("KA-2026-0001", "Balance Confirmation")
		self.assertEqual(found["findings"], ["Das Druckformat passt nicht zur Art dieses Dokuments."])
		self.assertEqual((found["text"], found["closing"]), ("", []))

	def test_an_english_statement(self):
		found = self.statement("KA-2026-0002", language="en")
		self.assertEqual(found["subject"], "Open items as of 25.11.2026")
		self.assertEqual(found["closing"], ["As of 25.11.2026, the balance is 1.680,00 € in our favour."])

	def test_the_letter_goes_to_the_address_of_the_party(self):
		with print_language("de"):
			frame = frappe.get_attr("briefbote.briefbote.receipt.briefbote_payment_letter")(
				frappe.get_doc("Party Statement", "KA-2026-0001")
			)
		self.assertEqual(frame["recipient"], ["Kunde Muster AG", "Hauptstraße 5", "54321 Beispielstadt"])

	def test_only_accounts_users_and_managers_may_read_a_statement(self):
		for role, allowed in (("Accounts User", True), ("Accounts Manager", True), ("Sales User", False)):
			with self.subTest(role=role):
				email = f"{role.lower().replace(' ', '-')}@statement.example"
				if not frappe.db.exists("User", email):
					user = frappe.get_doc(
						{"doctype": "User", "email": email, "first_name": role, "send_welcome_email": 0}
					).insert(ignore_permissions=True)
					user.add_roles(role)
				self.assertEqual(frappe.has_permission("Party Statement", "read", user=email), allowed)

	def test_the_print_format_renders_in_german_and_loads_nothing(self):
		with print_language("de"):
			html = frappe.get_print("Party Statement", "KA-2026-0001", "Kontoauszug", no_letterhead=0)
		self.assertIn("Kontoauszug KA-2026-0001", html)
		self.assertEqual(FETCHED.findall(LINK.sub("", SCRIPT.sub("", html))), [])
