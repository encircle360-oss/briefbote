"""Every text of the printouts of quotation and order confirmation reads in German, read from the files without a
bench (briefbote/translations/de.csv with the context Briefbote)."""

import re
from pathlib import Path
from unittest import TestCase

from briefbote.sales import offer, order
from briefbote.tests.test_translations import PRINTING_TEXT, printout_german

APP = Path(__file__).resolve().parents[1]
SALES = APP / "briefbote" / "sales.py"


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

	def test_the_titles_read_as_the_documents_they_are(self):
		german = printout_german()
		self.assertEqual((german[offer.TITLE], german[order.TITLE]), ("Angebot", "Auftragsbestätigung"))

	def test_no_german_text_of_a_quotation_or_confirmation_asks_for_a_transfer(self):
		german = printout_german()
		for text in (offer.VALID_UNTIL_ACCEPT, offer.ACCEPT, order.PAYMENT_TERM, order.TERM_DUE):
			with self.subTest(text=text):
				self.assertIsNone(re.search(r"überweisen|Rechnungsnummer", german[text]))
