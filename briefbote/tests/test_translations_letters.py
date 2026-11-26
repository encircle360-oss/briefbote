"""Every text of the Geschäftsbrief and of its entries in the menu reads in German, read from the files without a
bench (briefbote/translations/de.csv)."""

import json
from pathlib import Path
from unittest import TestCase

from briefbote.correspondence import letter
from briefbote.tests.test_translations import PRINTING_TEXT, desk_german, printout_german

APP = Path(__file__).resolve().parents[1]
CORRESPONDENCE = APP / "briefbote" / "correspondence.py"
MENU = APP / "briefbote" / "optional" / "menu.json"


class LetterTextsTest(TestCase):
	def test_every_text_of_the_letter_reads_in_german(self):
		texts = set(PRINTING_TEXT.findall(CORRESPONDENCE.read_text(encoding="utf-8"))) | {
			letter.OUR_REFERENCE,
			letter.DEPARTMENT,
			letter.NAME,
			letter.PHONE,
			letter.EMAIL,
			letter.DATE,
			letter.ADDRESSED,
			letter.UNADDRESSED,
			letter.FINDINGS_TITLE,
			letter.NO_ADDRESS,
			letter.EMPTY_BODY,
			letter.NO_SUBJECT,
		}
		self.assertEqual(sorted(texts - printout_german().keys()), [])

	def test_the_information_block_reads_as_din_5008_names_it(self):
		german = printout_german()
		self.assertEqual(
			[
				german[text]
				for text in (letter.OUR_REFERENCE, letter.NAME, letter.PHONE, letter.EMAIL, letter.DATE)
			],
			["Unser Zeichen", "Name", "Telefon", "E-Mail", "Datum"],
		)

	def test_the_date_of_the_page_line_never_breaks_from_its_vom(self):
		self.assertTrue(printout_german()[letter.ADDRESSED].endswith("vom\u00a0{1}"))
		self.assertTrue(printout_german()[letter.UNADDRESSED].endswith("vom\u00a0{0}"))

	def test_the_entries_of_the_menu_read_in_german(self):
		menu = json.loads(MENU.read_text(encoding="utf-8"))
		labels = {row["label"] for row in menu["sidebar"]} | {
			row["label"] for row in menu["workspace"]["shortcuts"]
		}
		self.assertEqual(sorted(labels - desk_german().keys()), [])
