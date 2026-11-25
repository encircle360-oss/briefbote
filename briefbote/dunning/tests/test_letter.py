from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.dunning import letter
from briefbote.dunning.letter import Charges, Level

D = Decimal


class LevelTest(TestCase):
	def test_each_level_has_its_title(self):
		self.assertEqual(
			[letter.level(number, ()).title for number in (1, 2, 3, 4, 7)],
			[
				letter.PAYMENT_REMINDER,
				letter.REMINDER,
				letter.SECOND_REMINDER,
				letter.FINAL_REMINDER,
				letter.FINAL_REMINDER,
			],
		)

	def test_the_settings_replace_title_text_and_days_of_a_level(self):
		own = (Level(2, "Erste Mahnung", "Bitte zahlen Sie bis {deadline}.", 5),)
		self.assertEqual(letter.level(2, own), own[0])
		self.assertEqual(letter.level(3, own).title, letter.SECOND_REMINDER)

	def test_a_row_of_the_settings_without_a_value_keeps_the_default_of_that_value(self):
		found = letter.level(1, (Level(1, "", "", 0),))
		self.assertEqual(found, letter.level(1, ()))

	def test_a_level_below_one_reads_as_the_first(self):
		self.assertEqual(letter.level(0, ()), letter.level(1, ()))

	def test_the_deadline_is_the_day_of_the_letter_and_the_days_of_its_level(self):
		self.assertEqual(letter.deadline(date(2026, 11, 25), letter.level(2, ())), date(2026, 12, 5))

	def test_the_texts_threaten_nothing_and_give_no_advice(self):
		for number in (1, 2, 3, 4):
			text = letter.level(number, ()).text.lower()
			with self.subTest(level=number):
				self.assertIn("{deadline}", text)
				for word in ("court", "lawyer", "collection", "legal", "credit agency"):
					self.assertNotIn(word, text)

	def test_the_text_names_its_deadline(self):
		self.assertEqual(
			letter.fill("Bis {deadline}, {deadline}.", "05.12.2026"), "Bis 05.12.2026, 05.12.2026."
		)


class AssessTest(TestCase):
	def test_a_payment_reminder_with_nothing_booked_claims_nothing(self):
		self.assertEqual(letter.assess(1, Charges(D(0), D(0), D(0), 0), consumer=False), ([], False, False))

	def test_a_payment_reminder_that_books_interest_or_a_fee_is_a_finding(self):
		self.assertEqual(
			letter.assess(1, Charges(D(5), D(0), D(9), 1), consumer=False),
			([letter.REMINDER_CHARGES], False, False),
		)

	def test_interest_at_or_below_the_lawful_maximum_is_claimed(self):
		self.assertEqual(
			letter.assess(2, Charges(D("12.34"), D(0), D("12.344"), 1), consumer=False), ([], True, False)
		)

	def test_interest_above_the_lawful_maximum_is_a_finding_instead_of_a_claim(self):
		self.assertEqual(
			letter.assess(2, Charges(D("12.36"), D(0), D("12.344"), 1), consumer=True),
			([letter.INTEREST_EXCEEDS], False, False),
		)

	def test_interest_whose_maximum_is_not_known_is_a_finding(self):
		self.assertEqual(
			letter.assess(2, Charges(D(1), D(0), None, 1), consumer=False),
			([letter.NO_BASE_RATE], False, False),
		)

	def test_the_lump_sum_is_claimed_from_a_business_in_default_up_to_forty_euro_a_claim(self):
		self.assertEqual(letter.assess(2, Charges(D(0), D(40), D(0), 1), consumer=False), ([], False, True))
		self.assertEqual(
			letter.assess(2, Charges(D(0), D(81), D(0), 2), consumer=False),
			([letter.FEE_EXCEEDS], False, False),
		)
		self.assertEqual(
			letter.assess(2, Charges(D(0), D(40), D(0), 0), consumer=False),
			([letter.FEE_NO_DEFAULT], False, False),
		)

	def test_a_consumer_owes_no_lump_sum(self):
		"""§ 288 Abs. 5 Satz 1 BGB: only a debtor who is not a consumer."""
		self.assertEqual(
			letter.assess(3, Charges(D(0), D(5), D(0), 1), consumer=True),
			([letter.FEE_CONSUMER], False, False),
		)

	def test_no_finding_text_gives_advice(self):
		for text in letter.FINDINGS:
			with self.subTest(text=text):
				self.assertNotIn("must pay", text)
