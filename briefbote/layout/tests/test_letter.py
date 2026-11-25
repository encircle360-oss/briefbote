from decimal import Decimal
from unittest import TestCase

from briefbote.layout import letter, metrics
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


class FootTest(TestCase):
	"""The foot: at most four blocks in the order address, contact, register and management, tax and bank, each at
	most four lines, in equal columns of the type area."""

	def test_gives_the_particulars_of_a_gmbh_in_four_blocks(self):
		self.assertEqual(
			letter.foot_blocks(COMPANY, german),
			[
				["Beispiel GmbH", "Musterweg 1", "12345 Musterstadt"],
				["Telefon +49 30 1234567", "info@beispiel.example", "www.beispiel.example"],
				# Court and managing directors wrap in a quarter of the type area; the registered office, the town of the
				# address, gives way so that the block keeps four lines.
				[
					"Amtsgericht\u00a0Musterstadt, HRB\u00a099999",
					"Geschäftsführer: Erika Mustermann, Max Mustermann",
				],
				[
					"USt-IdNr.: DE000000000",
					"Musterbank · BIC BYLADEM1001",
					"IBAN\u00a0DE02\u00a01203\u00a00000\u00a00000\u00a02020\u00a051",
				],
			],
		)

	def test_no_block_holds_more_than_four_lines_before_its_column_wraps_it(self):
		for company in (COMPANY, AG):
			with self.subTest(company=company.name):
				self.assertTrue(
					all(len(block) <= letter.FOOT_LINES for block in letter.foot_blocks(company, german))
				)

	def test_the_registered_office_gives_way_when_it_is_the_town_of_the_address_and_the_block_is_full(self):
		register = letter.foot_blocks(AG, german)[1]
		self.assertNotIn("Sitz: Musterstadt", register)
		self.assertIn("Vorstand: Erika Mustermann (Vorsitzende), Max Mustermann", register)
		self.assertIn("Vorsitz des Aufsichtsrats: Dr. Hans Beispiel", register)
		elsewhere = Company(
			name="Beispiel GmbH", city="Berlin", registered_office="Musterstadt", register_number="HRB 1"
		)
		self.assertEqual(letter.foot_blocks(elsewhere, german)[1], ["Sitz: Musterstadt", "HRB\u00a01"])

	def test_the_tax_number_stands_only_without_a_vat_id(self):
		self.assertEqual(
			letter.foot_blocks(Company(name="Beispiel GmbH", tax_number="12/345/67890"), german)[1],
			["Steuernummer: 12/345/67890"],
		)

	def test_the_vat_id_keeps_a_block_of_its_own_without_a_bank(self):
		company = Company(name="Beispiel GmbH", register_number="HRB 99999", vat_id="DE000000000")
		self.assertEqual(
			letter.foot_blocks(company, german),
			[["Beispiel GmbH"], ["HRB\u00a099999"], ["USt-IdNr.: DE000000000"]],
		)

	def test_the_foot_shows_the_first_bank_account(self):
		second = Bank(name="Zweite Bank", iban="DE89370400440532013000")
		company = Company(name="Beispiel GmbH", banks=(*COMPANY.banks, second))
		self.assertEqual(
			letter.foot_blocks(company, german)[1],
			[
				"Musterbank · BIC BYLADEM1001",
				"IBAN\u00a0DE02\u00a01203\u00a00000\u00a00000\u00a02020\u00a051",
			],
		)

	def test_a_long_bank_gives_its_vat_id_to_the_register_or_leaves_out_its_name(self):
		long = Bank(
			name="Volks- und Raiffeisenbank Musterstadt-Beispielhausen eG",
			iban="FR7630006000011234567890189",
			bic="GENODEF1XYZ",
		)
		small = Company(name="Beispiel GmbH", register_number="HRB 1", vat_id="DE000000000", banks=(long,))
		self.assertEqual(
			letter.foot_blocks(small, german)[1:],
			[
				["HRB\u00a01", "USt-IdNr.: DE000000000"],
				[
					"Volks- und Raiffeisenbank Musterstadt-Beispielhausen eG · BIC GENODEF1XYZ",
					"IBAN\u00a0FR76\u00a03000\u00a06000\u00a00112\u00a03456\u00a07890\u00a0189",
				],
			],
		)
		full = Company(
			name=COMPANY.name,
			street=COMPANY.street,
			pincode=COMPANY.pincode,
			city=COMPANY.city,
			phone=COMPANY.phone,
			email=COMPANY.email,
			website=COMPANY.website,
			registered_office=COMPANY.registered_office,
			register_court=COMPANY.register_court,
			register_number=COMPANY.register_number,
			managing_directors=COMPANY.managing_directors,
			vat_id=COMPANY.vat_id,
			banks=(long,),
		)
		self.assertEqual(
			letter.foot_blocks(full, german)[3],
			["USt-IdNr.: DE000000000", "BIC GENODEF1XYZ", "IBAN\u00a0FR76 3000 6000 0112 3456 7890 189"],
		)

	def test_a_long_bank_without_a_bic_keeps_its_name(self):
		long = Bank(
			name="Volks- und Raiffeisenbank Musterstadt-Beispielhausen eG", iban="FR7630006000011234567890189"
		)
		full = Company(
			name=COMPANY.name,
			phone=COMPANY.phone,
			register_court=COMPANY.register_court,
			register_number=COMPANY.register_number,
			managing_directors=COMPANY.managing_directors,
			executive_board=("Dr. Hans Beispiel",),
			vat_id=COMPANY.vat_id,
			tax_number=COMPANY.tax_number,
			banks=(long,),
		)
		self.assertIn(long.name, letter.foot_blocks(full, german)[-1])

	def test_a_bank_without_name_or_bic_prints_what_it_has(self):
		company = Company(name="Beispiel GmbH", banks=(Bank(iban="DE02 1203 0000 0000 2020 51"),))
		self.assertEqual(
			letter.foot_blocks(company, german)[1],
			["IBAN\u00a0DE02\u00a01203\u00a00000\u00a00000\u00a02020\u00a051"],
		)

	def test_leaves_out_empty_blocks(self):
		self.assertEqual(letter.foot_blocks(Company(name="Beispiel e.K."), german), [["Beispiel e.K."]])

	def test_a_line_wraps_at_its_spaces_and_counts_its_lines(self):
		self.assertEqual(letter.wrapped_lines(["kurz", "x" * 200], Decimal(40)), 2)
		words = " ".join(["Wort"] * 30)
		self.assertGreater(letter.wrapped_lines([words], Decimal(40)), 2)
		self.assertEqual(letter.wrapped_lines(["Erika\u00a0Mustermann"], Decimal(40)), 1)


AG = Company(
	name="Beispiel AG",
	street="Musterweg 1",
	pincode="12345",
	city="Musterstadt",
	registered_office="Musterstadt",
	register_court="Amtsgericht Musterstadt",
	register_number="HRB 88888",
	executive_board=("Erika Mustermann (Vorsitzende)", "Max Mustermann"),
	supervisory_chair="Dr. Hans Beispiel",
	vat_id="DE000000000",
)


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


class ReturnAddressTest(TestCase):
	LONG = Company(
		name="Holzbau und Innenausbau Rheinisch-Bergisches Land GmbH & Co. KG",
		street="Industriestraße 123, Gebäude C",
		pincode="12355",
		city="Musterstadt-Nord",
	)

	def test_a_short_return_address_stands_in_one_line_at_7_pt(self):
		found = letter.return_address(COMPANY)
		self.assertEqual(
			found,
			letter.ReturnAddress(("Beispiel GmbH · Musterweg 1 · 12345 Musterstadt",), Decimal(7), True),
		)

	def test_a_longer_one_is_set_smaller_but_not_below_6_pt(self):
		company = Company(
			name="Beispiel Sandbox A (TEST)",
			street="Am Musterberg 72",
			pincode="12355",
			city="Musterstadt",
		)
		found = letter.return_address(company)
		self.assertEqual(len(found.lines), 1)
		self.assertLess(found.size, Decimal(7))
		self.assertGreaterEqual(found.size, Decimal(6))
		self.assertTrue(found.fits)
		self.assertLessEqual(metrics.width(found.lines[0], found.size), letter.RETURN_WIDTH)

	def test_a_long_name_takes_a_line_of_its_own_and_keeps_postcode_and_town(self):
		found = letter.return_address(self.LONG)
		self.assertEqual(
			found.lines, (self.LONG.name, "Industriestraße 123, Gebäude C · 12355 Musterstadt-Nord")
		)
		self.assertTrue(found.fits)
		for line in found.lines:
			self.assertLessEqual(metrics.width(line, found.size), letter.RETURN_WIDTH)

	def test_what_does_not_fit_even_in_two_lines_says_so(self):
		found = letter.return_address(Company(name="Sehr " * 30 + "GmbH", city="Musterstadt"))
		self.assertEqual((found.size, found.fits), (Decimal(6), False))
		self.assertEqual(len(found.lines), 2)
		self.assertFalse(letter.return_address(Company(name="X" * 200)).fits)

	def test_a_company_without_particulars_has_no_return_address(self):
		self.assertEqual(letter.return_address(Company(name="")).lines, ())
