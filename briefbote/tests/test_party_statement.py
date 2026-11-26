"""The DocType Party Statement (Kontoauszug), read from its files without a bench: who may see it, its kinds and its
number series."""

import json
from pathlib import Path
from unittest import TestCase

from briefbote.statement import statement

DOCTYPE = (
	Path(__file__).resolve().parents[1] / "briefbote" / "doctype" / "party_statement" / "party_statement.json"
)
# The roles of ERPNext 16 that may open the reports a statement reads (the roles of
# erpnext/accounts/report/accounts_receivable/accounts_receivable.json and accounts_payable/accounts_payable.json):
# a statement of either kind shows what both show, so only who may see both may see it.
RECEIVABLE_ROLES = {"Accounts Manager", "Accounts User"}
PAYABLE_ROLES = {"Accounts User", "Purchase User", "Accounts Manager", "Auditor"}


def definition() -> dict:
	return json.loads(DOCTYPE.read_text(encoding="utf-8"))


def field(name: str) -> dict:
	return next(found for found in definition()["fields"] if found["fieldname"] == name)


class PermissionsTest(TestCase):
	def test_only_who_may_see_the_receivables_and_payables_may_see_a_statement(self):
		roles = {row["role"] for row in definition()["permissions"]}
		self.assertEqual(roles, RECEIVABLE_ROLES & PAYABLE_ROLES)

	def test_both_roles_may_write_submit_cancel_and_print_it(self):
		for row in definition()["permissions"]:
			with self.subTest(role=row["role"]):
				for right in ("read", "write", "create", "submit", "cancel", "amend", "print"):
					self.assertEqual(row.get(right), 1, right)


class DefinitionTest(TestCase):
	def test_a_statement_is_a_document_that_is_submitted(self):
		"""Only a submitted document keeps the rows it printed."""
		self.assertEqual(definition()["is_submittable"], 1)
		self.assertEqual(field("amended_from")["options"], "Party Statement")

	def test_its_kinds_are_those_of_the_core_which_gives_each_its_series(self):
		kinds = field("kind")["options"].split("\n")
		self.assertEqual(kinds, [statement.OPEN_ITEMS, statement.BALANCE_CONFIRMATION])
		self.assertEqual(definition()["autoname"], "naming_series:")

	def test_the_party_is_a_customer_or_a_supplier(self):
		self.assertEqual(field("party_type")["options"].split("\n"), ["Customer", "Supplier"])
		self.assertEqual(field("party")["options"], "party_type")

	def test_the_stored_rows_cannot_be_edited_by_hand(self):
		"""The rows come from the ledger, never from typing."""
		for name in ("items", "balances"):
			with self.subTest(table=name):
				self.assertEqual(field(name)["read_only"], 1)
