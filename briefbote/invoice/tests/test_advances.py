from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.invoice import advances
from briefbote.invoice.advances import Payment, Tax

SUPPLIED = date(2026, 12, 18)
RECEIVED = date(2026, 11, 27)


def taxed(allocated: str, credited: str = "3600.00", tax: str = "684.00", **fields) -> Payment:
	"""A payment entry with one tax line of 19 % on the paid amount, included in it, as ERPNext books an advance with
	„Advance Taxes and Charges“: it credits the customer the paid amount less the tax."""
	return Payment(
		"ZE-2026-0101",
		RECEIVED,
		Decimal(allocated),
		Decimal(credited),
		(Tax(Decimal(19), Decimal(tax)),),
		**fields,
	)


class SplitTest(TestCase):
	def test_an_advance_with_its_tax_included_deducts_consideration_tax_and_their_sum(self):
		"""UStAE 14.8 Abs. 7 Satz 1, Beispiel 1: each advance with its consideration and the tax on it."""
		found = advances.split(taxed("3600.00"))
		self.assertEqual(
			(found.net, found.rate, found.tax, found.gross),
			(Decimal("3600.00"), Decimal(19), Decimal("684.00"), Decimal("4284.00")),
		)
		self.assertTrue(found.known)

	def test_a_part_of_the_advance_deducts_its_share_of_the_tax(self):
		found = advances.split(taxed("1000.00"))
		self.assertEqual(
			(found.net, found.tax, found.gross), (Decimal("1000.00"), Decimal("190.00"), Decimal("1190.00"))
		)
		odd = advances.split(taxed("333.33"))
		self.assertEqual((odd.tax, odd.gross), (Decimal("63.33"), Decimal("396.66")))

	def test_a_payment_without_a_single_included_tax_line_deducts_only_what_was_allocated(self):
		"""Without the tax of the advance in the payment entry, Briefbote derives none: the gross amount alone."""
		cases = {
			"no tax": Payment("ZE-1", RECEIVED, Decimal(100), Decimal(100)),
			"on top": Payment(
				"ZE-2", RECEIVED, Decimal(100), Decimal(100), (Tax(Decimal(19), Decimal(19), included=False),)
			),
			"actual": Payment(
				"ZE-3",
				RECEIVED,
				Decimal(100),
				Decimal(100),
				(Tax(Decimal(19), Decimal(19), on_paid_amount=False),),
			),
			"deducted": Payment(
				"ZE-4", RECEIVED, Decimal(100), Decimal(100), (Tax(Decimal(19), Decimal(19), added=False),)
			),
			"no rate": Payment("ZE-5", RECEIVED, Decimal(100), Decimal(100), (Tax(Decimal(0), Decimal(19)),)),
			"two": Payment(
				"ZE-6",
				RECEIVED,
				Decimal(100),
				Decimal(74),
				(Tax(Decimal(19), Decimal(19)), Tax(Decimal(7), Decimal(7))),
			),
			"nothing credited": Payment(
				"ZE-7", RECEIVED, Decimal(100), Decimal(0), (Tax(Decimal(19), Decimal(19)),)
			),
		}
		for case, payment in cases.items():
			with self.subTest(case=case):
				found = advances.split(payment)
				self.assertEqual(
					(found.gross, found.net, found.tax, found.rate), (Decimal(100), None, None, None)
				)
				self.assertFalse(found.known)

	def test_a_tax_line_without_an_amount_does_not_count(self):
		payment = Payment(
			"ZE-8",
			RECEIVED,
			Decimal(100),
			Decimal(100),
			(Tax(Decimal(19), Decimal(19)), Tax(Decimal(7), Decimal(0))),
		)
		self.assertEqual(advances.split(payment).tax, Decimal("19.00"))


class AdvanceTest(TestCase):
	def test_only_a_payment_before_the_end_of_the_supply_is_an_advance(self):
		"""§ 14 Abs. 5 Satz 2 UStG: the Teilentgelte received before the supply."""
		self.assertTrue(advances.is_advance(RECEIVED, SUPPLIED))
		self.assertFalse(advances.is_advance(SUPPLIED, SUPPLIED))
		self.assertFalse(advances.is_advance(date(2026, 12, 20), SUPPLIED))


class SettleTest(TestCase):
	def test_an_invoice_with_an_advance_before_the_supply_is_a_final_invoice(self):
		found = advances.settle(Decimal("16088.80"), [taxed("3600.00")], SUPPLIED, charges_tax=True)
		self.assertTrue(found.final)
		self.assertEqual(found.title, advances.FINAL_INVOICE)
		self.assertEqual(
			(found.net, found.tax, found.gross, found.later, found.remainder),
			(Decimal("3600.00"), Decimal("684.00"), Decimal("4284.00"), Decimal(0), Decimal("11804.80")),
		)
		self.assertEqual(found.unsplit, [])

	def test_payments_after_the_supply_are_deducted_but_make_no_final_invoice(self):
		later = Payment("ZE-9", date(2026, 12, 20), Decimal(500), Decimal(500))
		found = advances.settle(Decimal("1190.00"), [later], SUPPLIED, charges_tax=True)
		self.assertFalse(found.final)
		self.assertEqual(found.title, "")
		self.assertEqual((found.later, found.remainder, found.unsplit), (Decimal(500), Decimal(690), []))

	def test_an_advance_without_its_tax_on_an_invoice_with_vat_is_named_for_a_finding(self):
		bare = Payment("JV-2026-0001", RECEIVED, Decimal(1000), Decimal(1000))
		found = advances.settle(Decimal("5000.00"), [taxed("3600.00"), bare], SUPPLIED, charges_tax=True)
		self.assertEqual(found.unsplit, ["JV-2026-0001"])
		self.assertEqual(found.gross, Decimal("5284.00"))
		self.assertIsNone(found.net)
		self.assertIsNone(found.tax)
		self.assertEqual(found.remainder, Decimal("-284.00"))

	def test_on_an_invoice_without_vat_an_advance_is_its_own_consideration(self):
		"""No tax arises, so the amount paid is the consideration and nothing is missing."""
		bare = Payment("ZE-10", RECEIVED, Decimal(1000), Decimal(1000))
		found = advances.settle(Decimal("3000.00"), [bare], SUPPLIED, charges_tax=False)
		deduction = found.advances[0]
		self.assertEqual((deduction.net, deduction.tax, deduction.rate), (Decimal(1000), Decimal(0), None))
		self.assertTrue(deduction.known)
		self.assertEqual((found.unsplit, found.net, found.tax), ([], Decimal(1000), Decimal(0)))

	def test_no_payments_settle_nothing(self):
		found = advances.settle(Decimal(100), [], SUPPLIED, charges_tax=True)
		self.assertEqual((found.final, found.remainder, found.gross), (False, Decimal(100), Decimal(0)))


class LabelTest(TestCase):
	def test_an_advance_names_its_day_and_payment_and_the_advance_invoice_where_it_is_known(self):
		self.assertEqual(advances.label(taxed("1.00")), (advances.ADVANCE, (RECEIVED, "ZE-2026-0101")))
		invoiced = taxed("1.00", invoice=("AZ-2026-0001", date(2026, 11, 23)))
		self.assertEqual(
			advances.label(invoiced),
			(advances.ADVANCE_INVOICED, (RECEIVED, "ZE-2026-0101", "AZ-2026-0001", date(2026, 11, 23))),
		)


class MatchTest(TestCase):
	def test_the_advance_invoice_of_a_payment_is_the_one_of_its_amount(self):
		candidates = [
			("AZ-1", date(2026, 11, 2), Decimal("4284.00")),
			("AZ-2", date(2026, 11, 3), Decimal("1190.00")),
		]
		self.assertEqual(advances.match(Decimal("4284.00"), candidates), ("AZ-1", date(2026, 11, 2)))
		self.assertEqual(advances.match(Decimal("4284.004"), candidates), ("AZ-1", date(2026, 11, 2)))

	def test_no_advance_invoice_or_two_of_the_amount_name_none(self):
		twice = [("AZ-1", date(2026, 11, 2), Decimal(100)), ("AZ-2", date(2026, 11, 3), Decimal(100))]
		self.assertIsNone(advances.match(Decimal(100), twice))
		self.assertIsNone(advances.match(Decimal(50), twice))
		self.assertIsNone(advances.match(Decimal(50), []))
