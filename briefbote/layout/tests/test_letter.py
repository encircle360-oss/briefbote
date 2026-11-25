from unittest import TestCase

from briefbote.layout import letter
from briefbote.layout.letter import Bank, Company, Party

GERMAN = {
	"Managing Directors:": "Geschäftsführer:",
	"Managing Director:": "Geschäftsführer:",
	"Registered Office: {0}": "Sitz: {0}",
	"Chair of the Supervisory Board: {0}": "Vorsitz des Aufsichtsrats: {0}",
	"Executive Board:": "Vorstand:",
	"VAT ID: {0}": "USt-IdNr.: {0}",
	"Tax Number: {0}": "Steuernummer: {0}",
	"Phone {0}": "Telefon {0}",
	"Germany": "Deutschland",
	"Austria": "Österreich",
}


def german(text: str) -> str:
	return GERMAN.get(text, text)


COMPANY = Company(
	name="Beispiel GmbH",
	street="Musterweg 1",
	pincode="12345",
	city="Musterstadt",
	country="Germany",
	phone="+49 30 1234567",
	email="info@beispiel.example",
	website="www.beispiel.example",
	registered_office="Musterstadt",
	register_court="Amtsgericht Musterstadt",
	register_number="HRB 99999",
	managing_directors=("Erika Mustermann", "Max Mustermann"),
	vat_id="DE000000000",
	tax_number="12/345/67890",
	banks=(Bank(name="Musterbank", iban="DE02120300000000202051", bic="BYLADEM1001"),),
)


class SenderLineTest(TestCase):
	def test_names_the_company_and_its_address_in_one_line(self):
		self.assertEqual(letter.sender_line(COMPANY), "Beispiel GmbH · Musterweg 1 · 12345 Musterstadt")

	def test_leaves_out_what_the_company_lacks(self):
		bare = Company(name="Beispiel GmbH")
		self.assertEqual(letter.sender_line(bare), "Beispiel GmbH")
		self.assertEqual(
			letter.sender_line(Company(name="Beispiel GmbH", city="Musterstadt")),
			"Beispiel GmbH · Musterstadt",
		)


class AddressTest(TestCase):
	def test_a_domestic_address_ends_with_postcode_and_town(self):
		party = Party(
			name="Kunde AG", street="Hauptstraße 5", pincode="54321", city="Beispielstadt", country="Germany"
		)
		self.assertEqual(
			letter.address_lines(party, "Germany", german),
			["Kunde AG", "Hauptstraße 5", "54321 Beispielstadt"],
		)

	def test_a_foreign_address_ends_with_the_country_in_capitals(self):
		party = Party(
			name="Kunde GmbH", street="Ringstraße 1", pincode="1010", city="Wien", country="Austria"
		)
		self.assertEqual(
			letter.address_lines(party, "Germany", german),
			["Kunde GmbH", "Ringstraße 1", "1010 Wien", "ÖSTERREICH"],
		)

	def test_names_the_contact_and_the_second_line_and_skips_what_is_empty(self):
		party = Party(
			name="Kunde AG",
			contact="Frau Dr. Erika Beispiel",
			street="Hauptstraße 5",
			street2="Gebäude B",
			pincode="",
			city="Beispielstadt",
		)
		self.assertEqual(
			letter.address_lines(party, "Germany", german),
			["Kunde AG", "Frau Dr. Erika Beispiel", "Hauptstraße 5", "Gebäude B", "Beispielstadt"],
		)

	def test_keeps_to_six_lines_by_joining_the_second_street_line_to_the_first(self):
		party = Party(
			name="Kunde AG",
			name2="Abteilung Einkauf",
			contact="Frau Erika Beispiel",
			street="Hauptstraße 5",
			street2="Gebäude B",
			pincode="1010",
			city="Wien",
			country="Austria",
		)
		lines = letter.address_lines(party, "Germany", german)
		self.assertEqual(len(lines), 6)
		self.assertEqual(lines[3], "Hauptstraße 5, Gebäude B")


class FooterTest(TestCase):
	def test_gives_the_particulars_of_a_gmbh_in_columns(self):
		columns = letter.footer_columns(COMPANY, german)
		self.assertEqual(
			columns,
			[
				[
					"Beispiel GmbH",
					"Musterweg 1",
					"12345 Musterstadt",
					"Telefon +49 30 1234567",
					"info@beispiel.example",
					"www.beispiel.example",
				],
				[
					"Sitz: Musterstadt",
					"Amtsgericht Musterstadt, HRB 99999",
					"Geschäftsführer:",
					"Erika Mustermann",
					"Max Mustermann",
				],
				["USt-IdNr.: DE000000000", "Steuernummer: 12/345/67890"],
				["Musterbank", "IBAN DE02 1203 0000 0000 2020 51", "BIC BYLADEM1001"],
			],
		)

	def test_names_the_board_and_its_chair_of_a_company_with_a_supervisory_board(self):
		company = Company(
			name="Beispiel AG",
			registered_office="Musterstadt",
			executive_board=("Erika Mustermann (Vorsitzende)", "Max Mustermann"),
			supervisory_chair="Dr. Hans Beispiel",
		)
		(column,) = letter.footer_columns(company, german)[1:2]
		self.assertEqual(
			column,
			[
				"Sitz: Musterstadt",
				"Vorstand:",
				"Erika Mustermann (Vorsitzende)",
				"Max Mustermann",
				"Vorsitz des Aufsichtsrats: Dr. Hans Beispiel",
			],
		)

	def test_leaves_out_empty_columns(self):
		self.assertEqual(letter.footer_columns(Company(name="Beispiel e.K."), german), [["Beispiel e.K."]])

	def test_a_register_number_without_a_court_stands_alone(self):
		company = Company(name="Beispiel GmbH", register_number="HRB 99999")
		self.assertEqual(letter.footer_columns(company, german)[1], ["HRB 99999"])

	def test_a_bank_without_name_or_bic_prints_what_it_has(self):
		company = Company(name="Beispiel GmbH", banks=(Bank(iban="DE02 1203 0000 0000 2020 51"),))
		self.assertEqual(letter.footer_columns(company, german)[1], ["IBAN DE02 1203 0000 0000 2020 51"])


class IbanTest(TestCase):
	def test_groups_an_iban_by_four(self):
		self.assertEqual(letter.iban("de02120300000000202051"), "DE02 1203 0000 0000 2020 51")
		self.assertEqual(letter.iban(" DE02 1203 0000 0000 2020 51 "), "DE02 1203 0000 0000 2020 51")
		self.assertEqual(letter.iban(""), "")


class DensityTest(TestCase):
	def test_an_address_that_fits_six_lines_at_ten_points_keeps_them(self):
		self.assertFalse(letter.dense(["Kunde AG", "Hauptstraße 5", "54321 Beispielstadt"]))
		self.assertFalse(letter.dense(["x" * letter.CHARACTERS_PER_LINE] * 6))

	def test_an_address_whose_lines_wrap_beyond_six_gets_smaller_type(self):
		lines = [
			"Holzbau und Innenausbau Rheinisch-Bergisches Land Beteiligungsgesellschaft mbH & Co. KG"
		] + ["z"] * 4
		self.assertTrue(letter.dense(lines))
		self.assertTrue(letter.dense(["x" * (letter.CHARACTERS_PER_LINE + 1)] + ["y"] * 5))
