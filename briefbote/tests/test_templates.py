"""The print formats, read without a bench: what they must not contain for the PDF generators of Frappe 16.

The Chromium-based generator opens a page of its own for a running head, an element with the id header-html, and
in Frappe 16.60.2 adds the header-spacing of the print CSS to its height as a string, which fails
(frappe/utils/pdf_generator/browser.py, set right in 16.61.0). Briefbote's stylesheet sets header-spacing, so no
template may give a printout such a head: the letterhead stands on the first page, the running line in the foot.
"""

from pathlib import Path
from unittest import TestCase

APP = Path(__file__).resolve().parents[1]
TEMPLATES = [*(APP / "templates").rglob("*.html"), *(APP / "briefbote" / "print_format").rglob("*.html")]


class TemplatesTest(TestCase):
	def test_no_template_gives_a_printout_a_running_head(self):
		self.assertTrue(TEMPLATES)
		for path in TEMPLATES:
			with self.subTest(template=path.name):
				self.assertNotIn('id="header-html"', path.read_text(encoding="utf-8"))


class PrintViewTest(TestCase):
	def test_the_print_view_prints_the_pdf_only_for_the_formats_of_briefbote(self):
		from briefbote import hooks

		self.assertEqual(hooks.page_js, {"print": "public/js/print_view.js"})
		script = (APP / hooks.page_js["print"]).read_text(encoding="utf-8")
		self.assertIn('const MODULE = "Briefbote";', script)
		self.assertIn("format.module === MODULE", script)
		self.assertIn("return this.briefbote_printit();", script)
