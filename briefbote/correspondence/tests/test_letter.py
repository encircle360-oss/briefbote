from unittest import TestCase

from briefbote.correspondence import letter
from briefbote.layout.letter import Party

GERMAN = {
	letter.OUR_REFERENCE: "Unser Zeichen",
	letter.NAME: "Name",
	letter.DEPARTMENT: "Abteilung",
	letter.PHONE: "Telefon",
	letter.EMAIL: "E-Mail",
	letter.DATE: "Datum",
	letter.ADDRESSED: "Brief an {0} vom {1}",
	letter.UNADDRESSED: "Brief vom {0}",
}


def german(text: str) -> str:
	return GERMAN.get(text, text)


class RecipientTest(TestCase):
	"""DIN 5008: the organisation in the first line, then the person; a private person alone in the first line."""

	def test_a_person_in_a_company_stands_below_the_company(self):
		party = letter.party(
			"Kunde Muster AG", "Erika Muster", street="Hauptstraße 5", pincode="12345", city="Musterstadt"
		)
		self.assertEqual(
			party,
			Party(
				name="Kunde Muster AG",
				contact="Erika Muster",
				street="Hauptstraße 5",
				pincode="12345",
				city="Musterstadt",
			),
		)

	def test_a_private_person_is_the_first_line(self):
		self.assertEqual(letter.party("", "Erika Muster").name, "Erika Muster")
		self.assertEqual(letter.party("", "Erika Muster").contact, "")

	def test_a_person_named_as_the_organisation_stands_once(self):
		self.assertEqual(letter.party("Erika Muster", "Erika Muster"), Party(name="Erika Muster"))

	def test_the_lines_of_an_address_abroad_end_with_the_country(self):
		party = letter.party(
			"Kunde Muster AG", "", street="Ring 1", pincode="1010", city="Wien", country="Austria"
		)
		self.assertEqual(
			letter.lines(party, "Germany", str.upper), ["Kunde Muster AG", "Ring 1", "1010 Wien", "AUSTRIA"]
		)


class PostalTest(TestCase):
	def test_an_address_needs_a_street_and_a_postcode_or_town(self):
		self.assertTrue(letter.postal(Party(name="A", street="Ring 1", city="Wien")))
		self.assertTrue(letter.postal(Party(name="A", street="Ring 1", pincode="1010")))
		self.assertFalse(letter.postal(Party(name="A", street="Ring 1")))
		self.assertFalse(letter.postal(Party(name="A", city="Wien")))
		self.assertFalse(letter.postal(Party(name="A")))


class InformationTest(TestCase):
	"""The information block of DIN 5008: Unser Zeichen, then the person to contact, Datum last."""

	def test_the_rows_stand_in_the_order_of_din_5008(self):
		rows = letter.information(
			german,
			reference="Ausgangsrechnung RE-2026-0101",
			department="Vertrieb",
			name="Erika Mustermann",
			phone="+49 30 1234567",
			email="erika@beispiel.example",
			date="26.11.2026",
		)
		self.assertEqual(
			rows,
			[
				("Unser Zeichen", "Ausgangsrechnung RE-2026-0101"),
				("Abteilung", "Vertrieb"),
				("Name", "Erika Mustermann"),
				("Telefon", "+49 30 1234567"),
				("E-Mail", "erika@beispiel.example"),
				("Datum", "26.11.2026"),
			],
		)

	def test_a_row_without_a_value_is_left_out(self):
		self.assertEqual(letter.information(german, date="26.11.2026"), [("Datum", "26.11.2026")])

	def test_without_a_person_to_contact_the_block_names_no_phone_or_mail(self):
		"""The foot names the phone and mail of the company; in the block they belong to the person."""
		self.assertEqual(
			letter.information(german, phone="+49 30 1", email="info@beispiel.example", date="26.11.2026"),
			[("Datum", "26.11.2026")],
		)


class RunningTitleTest(TestCase):
	def test_names_the_recipient_and_the_date(self):
		self.assertEqual(
			letter.running_title("Kunde Muster AG", "26.11.2026", german),
			"Brief an Kunde Muster AG vom 26.11.2026",
		)

	def test_without_a_recipient_names_the_date(self):
		self.assertEqual(letter.running_title("", "26.11.2026", german), "Brief vom 26.11.2026")

	def test_a_long_name_is_cut_at_a_word(self):
		title = letter.running_title(
			"Sehr lange Firma mit einem Namen über viele Wörter GmbH & Co. KG", "26.11.2026", german
		)
		self.assertEqual(title, "Brief an Sehr lange Firma mit einem Namen über… vom 26.11.2026")

	def test_a_long_word_is_cut_where_it_must(self):
		title = letter.running_title("A" * 60, "1.1.2027", german)
		self.assertEqual(title, f"Brief an {'A' * 40}… vom 1.1.2027")


class FindingsTest(TestCase):
	def test_a_letter_without_postal_address_or_text_is_incomplete(self):
		self.assertEqual(letter.findings(postal=False, text=False), [letter.NO_ADDRESS, letter.EMPTY_BODY])
		self.assertEqual(letter.findings(postal=True, text=True), [])

	def test_a_missing_subject_is_a_warning_not_a_finding(self):
		self.assertNotIn(letter.NO_SUBJECT, letter.findings(postal=True, text=True))
		self.assertTrue(letter.warns_without_subject(" "))
		self.assertTrue(letter.warns_without_subject(None))
		self.assertFalse(letter.warns_without_subject("Ihre Anfrage"))


class LongValueTest(TestCase):
	"""An e-mail address has no space to wrap at; one wider than the column of the values breaks before its @."""

	def test_a_long_address_breaks_before_its_at(self):
		rows = letter.information(
			german,
			name="Max Mustermann",
			email="max.mustermann@beispiel.example",
			reference="Ausgangsrechnung RE-1",
		)
		self.assertIn(("E-Mail", "max.mustermann"), rows)
		self.assertEqual(rows[rows.index(("E-Mail", "max.mustermann")) + 1], ("", "@beispiel.example"))

	def test_a_short_address_stays_on_one_line(self):
		rows = letter.information(german, name="Max Mustermann", email="max@beispiel.example")
		self.assertIn(("E-Mail", "max@beispiel.example"), rows)

	def test_a_long_value_without_an_at_stays_as_it_is(self):
		rows = letter.information(german, reference="A" * 60)
		self.assertEqual(rows, [("Unser Zeichen", "A" * 60)])
