from unittest import TestCase

from briefbote.layout import medium


class MediumTest(TestCase):
	def test_the_preview_of_the_print_view_is_the_screen(self):
		self.assertEqual(medium.medium("/api/method/frappe.www.printview.get_html_and_style"), medium.SCREEN)

	def test_the_page_printview_is_printed_by_the_browser(self):
		self.assertEqual(medium.medium("/printview"), medium.BROWSER)

	def test_everything_else_goes_through_a_pdf_generator(self):
		for path in (
			None,
			"",
			"/api/method/frappe.utils.print_format.download_pdf",
			"/api/method/frappe.utils.print_format.download_multi_pdf",
			"/api/method/frappe.core.doctype.communication.email.make",
		):
			with self.subTest(path=path):
				self.assertEqual(medium.medium(path), medium.PDF)


class CounterTest(TestCase):
	def test_the_page_line_of_the_browser_counts_its_pages(self):
		self.assertEqual(
			medium.page_counter("Rechnung RE-1", "Seite {0} von {1}"),
			'"Rechnung RE-1 \\B7  Seite " counter(page) " von " counter(pages)',
		)

	def test_quotes_and_backslashes_cannot_end_the_string(self):
		self.assertEqual(
			medium.page_counter('A "B" \\ C', "Page {0} of {1}"),
			'"A \\22 B\\22  \\5C  C \\B7  Page " counter(page) " of " counter(pages)',
		)

	def test_a_label_without_the_total_counts_the_page_alone(self):
		self.assertEqual(medium.page_counter("X", "S. {0}"), '"X \\B7  S. " counter(page) ""')

	def test_text_after_the_total_follows_it(self):
		self.assertEqual(
			medium.page_counter("X", "{0}/{1} Seiten"),
			'"X \\B7  " counter(page) "/" counter(pages) " Seiten"',
		)
