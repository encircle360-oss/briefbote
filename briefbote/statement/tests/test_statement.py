from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.statement import statement


def row(**fields) -> dict:
	"""A row as ERPNext's report Accounts Receivable or Accounts Payable returns it."""
	return {
		"voucher_type": "Sales Invoice",
		"voucher_no": "RE-1",
		"posting_date": date(2026, 9, 1),
		"due_date": date(2026, 9, 15),
		"invoiced": 100.0,
		"paid": 0.0,
		"credit_note": 0.0,
		"outstanding": 100.0,
		"currency": "EUR",
		**fields,
	}


class ItemTest(TestCase):
	def test_an_item_keeps_the_amounts_of_the_report(self):
		found = statement.item(row(invoiced=2380.0, paid=1880.0, outstanding=500.0))
		self.assertEqual(
			(found.invoiced, found.paid, found.outstanding),
			(Decimal("2380"), Decimal("1880"), Decimal("500")),
		)

	def test_credits_count_as_paid(self):
		found = statement.item(row(invoiced=100.0, paid=20.0, credit_note=30.0, outstanding=50.0))
		self.assertEqual(found.paid, Decimal("50"))

	def test_the_partner_s_own_number_is_the_bill_number_or_the_order_of_the_customer(self):
		self.assertEqual(statement.item(row(bill_no="RG-7", po_no="")).reference, "RG-7")
		self.assertEqual(statement.item(row(po_no="PO-4711")).reference, "PO-4711")
		self.assertEqual(statement.item(row()).reference, "")

	def test_each_voucher_is_named_by_its_kind(self):
		self.assertEqual(statement.item(row()).kind, statement.INVOICE)
		self.assertEqual(statement.item(row(is_return=1)).kind, statement.CORRECTION)
		self.assertEqual(statement.item(row(voucher_type="Purchase Invoice")).kind, statement.INVOICE)
		self.assertEqual(statement.item(row(voucher_type="Payment Entry")).kind, statement.PAYMENT)
		self.assertEqual(statement.item(row(voucher_type="Journal Entry")).kind, statement.BOOKING)
		self.assertEqual(statement.item(row(voucher_type="Dunning")).kind, statement.OTHER)

	def test_items_stand_in_the_order_of_their_dates_and_numbers(self):
		found = statement.items(
			[
				row(voucher_no="RE-3", posting_date=date(2026, 10, 1)),
				row(voucher_no="RE-2", posting_date=date(2026, 9, 1)),
				row(voucher_no="RE-1", posting_date=date(2026, 9, 1)),
			]
		)
		self.assertEqual([item.voucher_no for item in found], ["RE-1", "RE-2", "RE-3"])

	def test_rows_without_a_voucher_are_no_items(self):
		"""A total or an empty row of a report has no voucher."""
		self.assertEqual(statement.items([{}, {"voucher_no": ""}, row()])[0].voucher_no, "RE-1")
		self.assertEqual(len(statement.items([{}, row()])), 1)


class BalanceTest(TestCase):
	def test_each_currency_has_its_own_balance(self):
		"""Amounts of different currencies are never added up."""
		found = statement.balances(
			statement.items(
				[
					row(voucher_no="RE-1", invoiced=100.0, outstanding=100.0),
					row(voucher_no="RE-2", invoiced=50.0, paid=20.0, outstanding=30.0),
					row(voucher_no="RE-3", invoiced=70.0, outstanding=70.0, currency="USD"),
				]
			)
		)
		self.assertEqual(
			[(b.currency, b.invoiced, b.paid, b.outstanding) for b in found],
			[("EUR", Decimal(150), Decimal(20), Decimal(130)), ("USD", Decimal(70), Decimal(0), Decimal(70))],
		)

	def test_no_items_no_balances(self):
		self.assertEqual(statement.balances([]), [])

	def test_the_balance_of_a_customer_is_in_our_favour_when_it_owes(self):
		self.assertEqual(statement.favour("Customer", Decimal(10)), statement.OURS)
		self.assertEqual(statement.favour("Customer", Decimal(-10)), statement.YOURS)
		self.assertEqual(statement.favour("Customer", Decimal(0)), statement.BALANCED)

	def test_the_balance_of_a_supplier_is_in_its_favour_when_we_owe(self):
		"""The report Accounts Payable shows what is owed to a supplier as a positive amount."""
		self.assertEqual(statement.favour("Supplier", Decimal(10)), statement.YOURS)
		self.assertEqual(statement.favour("Supplier", Decimal(-10)), statement.OURS)
		self.assertEqual(statement.favour("Supplier", Decimal(0)), statement.BALANCED)


class KindTest(TestCase):
	def test_each_kind_has_its_series_and_title(self):
		self.assertEqual(statement.series(statement.OPEN_ITEMS), "KA-.YYYY.-.####")
		self.assertEqual(statement.series(statement.BALANCE_CONFIRMATION), "SB-.YYYY.-.####")
		self.assertEqual(statement.title(statement.OPEN_ITEMS), statement.STATEMENT_TITLE)
		self.assertEqual(statement.title(statement.BALANCE_CONFIRMATION), statement.CONFIRMATION_TITLE)

	def test_a_statement_states_only_as_a_submitted_document_of_its_kind(self):
		self.assertTrue(statement.states(statement.OPEN_ITEMS, statement.OPEN_ITEMS, 1))
		self.assertFalse(statement.states(statement.OPEN_ITEMS, statement.BALANCE_CONFIRMATION, 1))
		self.assertFalse(statement.states(statement.OPEN_ITEMS, statement.OPEN_ITEMS, 2))

	def test_a_draft_shows_the_ledger_as_it_is_now(self):
		"""A draft reads the ledger on each print; a submitted document prints what it stored."""
		self.assertTrue(statement.reads_ledger(0))
		self.assertFalse(statement.reads_ledger(1))
		self.assertFalse(statement.reads_ledger(2))
		self.assertTrue(statement.states(statement.OPEN_ITEMS, statement.OPEN_ITEMS, 0))


class ConfirmationTest(TestCase):
	def test_only_a_submitted_balance_confirmation_asks_for_a_reply(self):
		"""A draft or a cancelled request must not be answered; neither must a statement of the other kind."""
		BC = statement.BALANCE_CONFIRMATION
		self.assertTrue(statement.asks(BC, BC, 1))
		self.assertFalse(statement.asks(BC, BC, 0))
		self.assertFalse(statement.asks(BC, BC, 2))
		self.assertFalse(statement.asks(statement.OPEN_ITEMS, BC, 1))
		self.assertFalse(statement.asks(statement.OPEN_ITEMS, statement.OPEN_ITEMS, 1))

	def test_the_request_names_the_deadline_where_there_is_one(self):
		self.assertEqual(statement.request(True), statement.REQUEST_BY)
		self.assertEqual(statement.request(False), statement.REQUEST)
		self.assertEqual(statement.REQUEST_BY.count("{"), 1)

	def test_the_reply_names_the_creditor_not_a_side(self):
		"""The confirming party writes the reply; „in our favour“ would turn around in its mouth, so the reply names
		whom the balance favours."""
		self.assertEqual(
			statement.beneficiary("Customer", Decimal(10), "Beispiel GmbH", "Kunde AG"), "Beispiel GmbH"
		)
		self.assertEqual(
			statement.beneficiary("Customer", Decimal(-10), "Beispiel GmbH", "Kunde AG"), "Kunde AG"
		)
		self.assertEqual(
			statement.beneficiary("Supplier", Decimal(10), "Beispiel GmbH", "Lieferant KG"), "Lieferant KG"
		)
		self.assertEqual(statement.beneficiary("Supplier", Decimal(0), "Beispiel GmbH", "Lieferant KG"), "")

	def test_a_balanced_account_is_confirmed_without_an_amount(self):
		self.assertEqual(statement.confirmation(Decimal(0)), statement.CONFIRM_BALANCED)
		self.assertEqual(statement.confirmation(Decimal(5)), statement.CONFIRM)
		self.assertEqual(statement.CONFIRM.count("{"), 3)
