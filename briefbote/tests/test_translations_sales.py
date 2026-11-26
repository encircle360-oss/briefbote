"""Every text of the printouts of quotation and order confirmation reads in German, read from the files without a
bench (briefbote/translations/de.csv with the context Briefbote)."""

import re
from pathlib import Path
from unittest import TestCase

from briefbote.dunning import interest, letter
from briefbote.purchase import order as purchase_order
from briefbote.purchase import request, returns
from briefbote.sales import delivery, offer, order, packing, receipt
from briefbote.tests.test_translations import PRINTING_TEXT, printout_german

APP = Path(__file__).resolve().parents[1]
SALES = APP / "briefbote" / "sales.py"
DUNNING = APP / "briefbote" / "dunning.py"
RECEIPT = APP / "briefbote" / "receipt.py"
PURCHASE = APP / "briefbote" / "purchase.py"


class SalesTextsTest(TestCase):
	def test_every_text_of_the_sales_module_reads_in_german(self):
		texts = set(PRINTING_TEXT.findall(SALES.read_text(encoding="utf-8")))
		self.assertTrue(texts)
		self.assertEqual(sorted(texts - printout_german().keys()), [])

	def test_every_title_label_and_notice_of_quotation_and_order_confirmation_reads_in_german(self):
		texts = {
			offer.TITLE,
			offer.ALTERNATIVE,
			offer.ALTERNATIVE_ALONE,
			offer.UNIT_PRICE,
			offer.VALID_UNTIL,
			offer.VALID_UNTIL_ACCEPT,
			offer.ACCEPT,
			order.TITLE,
			order.OUR_QUOTATION,
			order.SCHEDULED_DELIVERY,
			order.SCHEDULED_DELIVERIES,
			order.POSITION_DELIVERY,
			order.PAYMENT_TERM,
			order.PAYMENT_TERMS,
			order.TERM_TEXT,
			order.TERM_DUE,
			order.INVOICE_FOLLOWS,
		}
		self.assertEqual(sorted(texts - printout_german().keys()), [])

	def test_every_title_label_and_line_of_the_delivery_note_reads_in_german(self):
		texts = {
			delivery.TITLE,
			delivery.RETURN_TITLE,
			delivery.DATE,
			delivery.DELIVERY_DATE,
			delivery.SERIAL_NUMBER,
			delivery.SERIAL_NUMBERS,
			delivery.BATCH,
			delivery.BATCHES,
			delivery.RECEIVED,
			delivery.NET_WEIGHT,
			delivery.OUR_ORDER,
			*delivery.SIGNATURE_FIELDS,
		}
		self.assertEqual(sorted(texts - printout_german().keys()), [])
		self.assertEqual(printout_german()[delivery.TITLE], "Lieferschein")

	def test_every_text_of_the_dunning_module_reads_in_german(self):
		texts = set(PRINTING_TEXT.findall(DUNNING.read_text(encoding="utf-8")))
		self.assertTrue(texts)
		self.assertEqual(sorted(texts - printout_german().keys()), [])

	def test_every_title_text_and_finding_of_a_dunning_letter_reads_in_german(self):
		texts = {
			letter.PAYMENT_REMINDER,
			letter.REMINDER,
			letter.SECOND_REMINDER,
			letter.FINAL_REMINDER,
			letter.TEXT_1,
			letter.TEXT_2,
			letter.TEXT_3,
			letter.TEXT_4,
			*letter.FINDINGS,
		}
		german = printout_german()
		self.assertEqual(sorted(texts - german.keys()), [])
		self.assertEqual(
			[
				german[title]
				for title in (
					letter.PAYMENT_REMINDER,
					letter.REMINDER,
					letter.SECOND_REMINDER,
					letter.FINAL_REMINDER,
				)
			],
			["Zahlungserinnerung", "Mahnung", "2. Mahnung", "Letzte Mahnung"],
		)
		for text in (letter.TEXT_1, letter.TEXT_2, letter.TEXT_3, letter.TEXT_4):
			with self.subTest(text=text):
				self.assertIn("{deadline}", german[text])

	def test_the_warning_of_the_check_reads_in_german(self):
		from briefbote.tests.test_translations import desk_german

		self.assertIn(interest.NO_BASE_RATE_TODAY, desk_german())

	def test_every_text_of_the_payment_confirmation_reads_in_german(self):
		texts = set(PRINTING_TEXT.findall(RECEIPT.read_text(encoding="utf-8"))) | {
			receipt.TITLE,
			receipt.RECEIPT_TITLE,
			receipt.RECEIVED,
			receipt.APPLIED,
			receipt.UNALLOCATED,
			receipt.NOT_CONFIRMED,
			receipt.INVOICE,
			receipt.ORDER,
			receipt.DUNNING,
			receipt.OTHER,
		}
		german = printout_german()
		self.assertEqual(sorted(texts - german.keys()), [])
		self.assertEqual(
			(german[receipt.TITLE], german[receipt.RECEIPT_TITLE]), ("Zahlungsbestätigung", "Quittung")
		)

	def test_every_text_of_the_purchase_order_reads_in_german(self):
		texts = set(PRINTING_TEXT.findall(PURCHASE.read_text(encoding="utf-8"))) | {
			purchase_order.TITLE,
			purchase_order.CONFIRM,
			purchase_order.DELIVERY_ADDRESS,
			purchase_order.SUPPLIER_PART,
		}
		german = printout_german()
		self.assertEqual(sorted(texts - german.keys()), [])
		self.assertEqual(german[purchase_order.TITLE], "Bestellung")

	def test_every_text_of_the_request_for_quotation_reads_in_german(self):
		texts = {
			request.TITLE,
			request.NUMBER,
			request.REQUIRED_BY,
			request.POSITION_REQUIRED,
			request.OUR_PART,
			request.SUPPLIER_PART,
			request.UNIT_PRICE,
			request.ASK_PRICES,
			request.ASK_DATES,
			request.ASK_INCOTERM,
			request.NO_SUPPLIER,
			request.NOT_LISTED,
			request.FINDINGS_TITLE,
		}
		german = printout_german()
		self.assertEqual(sorted(texts - german.keys()), [])
		self.assertEqual(german[request.TITLE], "Anfrage")

	def test_every_text_of_the_return_to_the_supplier_reads_in_german(self):
		texts = {
			returns.TITLE,
			returns.GOODS_RECEIPT,
			returns.SUPPLIER_DELIVERY_NOTE,
			returns.OUR_PURCHASE_ORDER,
			returns.CARRIER,
			returns.SUBJECT,
			returns.REJECTED,
			returns.REJECTED_PART,
			returns.PICK_UP,
			returns.TAKEN_OVER,
			returns.NOT_A_RETURN,
			returns.FINDINGS_TITLE,
		}
		german = printout_german()
		self.assertEqual(sorted(texts - german.keys()), [])
		self.assertEqual(german[returns.TITLE], "Rücksendung")

	def test_every_text_of_the_packing_list_reads_in_german(self):
		texts = {
			packing.TITLE,
			packing.PACKAGE,
			packing.PACKAGES,
			packing.SUBJECT,
			packing.PACKAGE_COUNT,
			packing.NET,
			packing.GROSS,
			packing.TOTAL,
			packing.PACKAGE_HEAD,
		}
		german = printout_german()
		self.assertEqual(sorted(texts - german.keys()), [])
		self.assertEqual(german[packing.TITLE], "Packliste")

	def test_a_date_never_breaks_from_its_vom(self):
		"""„… vom 26.11.2026“ in an information block breaks before „vom“ if at all, never between it and the date."""
		self.assertEqual(printout_german()["{0} of {1}"], "{0} vom\u00a0{1}")

	def test_the_titles_read_as_the_documents_they_are(self):
		german = printout_german()
		self.assertEqual((german[offer.TITLE], german[order.TITLE]), ("Angebot", "Auftragsbestätigung"))

	def test_no_german_text_of_a_quotation_or_confirmation_asks_for_a_transfer(self):
		german = printout_german()
		for text in (offer.VALID_UNTIL_ACCEPT, offer.ACCEPT, order.PAYMENT_TERM, order.TERM_DUE):
			with self.subTest(text=text):
				self.assertIsNone(re.search(r"überweisen|Rechnungsnummer", german[text]))
