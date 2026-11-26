from unittest import TestCase

from briefbote.sales import receipt


class ConfirmsTest(TestCase):
	def test_only_a_submitted_receipt_from_a_customer_is_confirmed(self):
		"""§ 368 Satz 1 BGB: the creditor acknowledges what it has received; § 370 BGB lets whoever brings a receipt
		collect the payment, so nothing unbooked is confirmed."""
		self.assertTrue(receipt.confirms("Receive", "Customer", 1))
		self.assertFalse(receipt.confirms("Receive", "Customer", 0))
		self.assertFalse(receipt.confirms("Receive", "Customer", 2))
		self.assertFalse(receipt.confirms("Pay", "Supplier", 1))
		self.assertFalse(receipt.confirms("Receive", "Employee", 1))
		self.assertFalse(receipt.confirms("Internal Transfer", "", 1))


class DirectionTest(TestCase):
	def test_only_a_payment_received_from_a_customer_has_documents_to_confirm(self):
		"""A payment to a supplier lists nothing a customer could have paid."""
		self.assertTrue(receipt.from_customer("Receive", "Customer"))
		self.assertFalse(receipt.from_customer("Pay", "Supplier"))
		self.assertFalse(receipt.from_customer("Receive", "Employee"))


class KindsTest(TestCase):
	def test_each_reference_is_named_by_its_kind(self):
		self.assertEqual(receipt.kind("Sales Invoice"), receipt.INVOICE)
		self.assertEqual(receipt.kind("Sales Order"), receipt.ORDER)
		self.assertEqual(receipt.kind("Dunning"), receipt.DUNNING)
		self.assertEqual(receipt.kind("Journal Entry"), receipt.OTHER)

	def test_the_titles_differ_for_the_confirmation_and_the_receipt(self):
		self.assertEqual(receipt.title(False), receipt.TITLE)
		self.assertEqual(receipt.title(True), receipt.RECEIPT_TITLE)


class TextsTest(TestCase):
	def test_the_receipt_acknowledges_amount_day_and_payer(self):
		self.assertEqual(receipt.RECEIVED.count("{"), 3)
		self.assertIn("received", receipt.RECEIVED)

	def test_no_text_asks_for_payment(self):
		for text in (
			receipt.TITLE,
			receipt.RECEIPT_TITLE,
			receipt.RECEIVED,
			receipt.APPLIED,
			receipt.UNALLOCATED,
		):
			with self.subTest(text=text):
				self.assertNotIn("transfer", text.lower())
