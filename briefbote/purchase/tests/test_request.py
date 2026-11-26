from datetime import date
from unittest import TestCase

from briefbote.purchase import request


class SupplierTest(TestCase):
	"""ERPNext prints a Request for Quotation for one supplier of its list at a time, the one in its field vendor
	(update_supplier_part_no and before_print in erpnext/buying/doctype/request_for_quotation)."""

	def test_the_request_goes_to_the_supplier_erpnext_prints_it_for(self):
		self.assertEqual(request.supplier_findings("S-1", ["S-1", "S-2"]), [])

	def test_a_request_without_a_supplier_addresses_nobody_and_says_so(self):
		self.assertEqual(request.supplier_findings("", []), [(request.NO_SUPPLIER, ())])
		self.assertEqual(request.supplier_findings(None, ["S-1"]), [(request.NO_SUPPLIER, ())])

	def test_a_supplier_outside_the_list_is_a_finding(self):
		self.assertEqual(request.supplier_findings("S-9", ["S-1"]), [(request.NOT_LISTED, ("S-9",))])


class RequiredTest(TestCase):
	def test_the_days_the_positions_are_required_by_from_first_to_last(self):
		first, last = date(2026, 12, 8), date(2026, 12, 22)
		self.assertEqual(request.required(None, [last, None, first, first]), (first, last))
		self.assertEqual(request.required(date(2026, 12, 1), [first]), (first,))

	def test_one_day_reads_required_by_and_a_span_as_the_required_dates(self):
		self.assertEqual(request.required_label((date(2026, 12, 8),)), request.REQUIRED_BY)
		self.assertEqual(
			request.required_label((date(2026, 12, 8), date(2026, 12, 22))), request.REQUIRED_DATES
		)

	def test_without_dates_of_its_positions_the_date_of_the_request(self):
		self.assertEqual(request.required(date(2026, 12, 1), [None]), (date(2026, 12, 1),))
		self.assertEqual(request.required(None, []), ())


class MessageTest(TestCase):
	def test_the_message_for_the_supplier_prints_as_its_text(self):
		self.assertEqual(
			request.message("Bitte bieten Sie uns an:\n", use_html=False), "Bitte bieten Sie uns an:"
		)

	def test_a_template_of_the_email_or_html_is_not_printed(self):
		"""ERPNext renders the message as a Jinja template for the e-mail (supplier_rfq_mail); on paper its
		placeholders would stand as they are."""
		self.assertEqual(request.message("Guten Tag {{ supplier_name }}", use_html=False), "")
		self.assertEqual(request.message("{% if x %}a{% endif %}", use_html=False), "")
		self.assertEqual(request.message("Text", use_html=True), "")
		self.assertEqual(request.message(None, use_html=False), "")


class PositionTest(TestCase):
	def test_our_and_the_suppliers_item_number_where_known(self):
		self.assertEqual(
			request.item_numbers("GK-125", "Gipskartonplatte", "L-0001"),
			[(request.OUR_PART, ("GK-125",)), (request.SUPPLIER_PART, ("L-0001",))],
		)

	def test_an_item_number_that_is_the_name_is_not_repeated(self):
		self.assertEqual(request.item_numbers("Schrauben", "Schrauben", None), [])
		self.assertEqual(request.item_numbers(None, "Schrauben", ""), [])

	def test_a_position_without_a_quantity_asks_for_the_price_per_unit(self):
		"""ERPNext 16 allows a quantity of 0 in a request where the Buying Settings permit it
		(set_has_unit_price_items)."""
		self.assertEqual(request.unit_price_note(0), [(request.UNIT_PRICE, ())])
		self.assertEqual(request.unit_price_note(3), [])


class ClosingTest(TestCase):
	def test_a_request_asks_for_what_its_data_name(self):
		self.assertEqual(
			request.closing(True, required=True, incoterm="FCA Musterstadt"),
			[(request.ASK_PRICES, ()), (request.ASK_DATES, ()), (request.ASK_INCOTERM, ("FCA Musterstadt",))],
		)
		self.assertEqual(request.closing(True, required=False, incoterm=""), [(request.ASK_PRICES, ())])

	def test_a_draft_or_cancelled_request_asks_nothing(self):
		self.assertEqual(request.closing(False, required=True, incoterm="FCA"), [])

	def test_the_delivery_terms_read_as_code_and_place(self):
		self.assertEqual(request.delivery_terms("FCA", "Musterstadt"), "FCA Musterstadt")
		self.assertEqual(request.delivery_terms("EXW", ""), "EXW")
		self.assertEqual(request.delivery_terms("", "Musterstadt"), "")

	def test_the_title_is_that_of_a_request_for_quotation(self):
		self.assertEqual(request.TITLE, "Request for Quotation")
