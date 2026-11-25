from datetime import date
from decimal import Decimal
from unittest import TestCase

from briefbote.annex import timesheets
from briefbote.annex.timesheets import Entry, Person

D = Decimal


def entry(day: int, person: str, project: str, hours: str, task: str = "") -> Entry:
	return Entry(
		day=date(2026, 11, day),
		person=person,
		activity="Beratung",
		description="Workshop",
		project=project,
		task=task,
		hours=D(hours),
	)


ENTRIES = [
	entry(12, "Max Mustermann", "Datenmigration", "3.5"),
	entry(3, "Erika Mustermann", "Einführung", "8", "Konzept"),
	entry(3, "Max Mustermann", "Einführung", "4.25"),
	entry(5, "Erika Mustermann", "Datenmigration", "2"),
]


class PersonTest(TestCase):
	def test_a_person_prints_by_name_initials_or_role(self):
		self.assertEqual(timesheets.person("Erika Mustermann", "Beraterin", Person.NAME), "Erika Mustermann")
		self.assertEqual(timesheets.person("Erika Mustermann", "Beraterin", Person.INITIALS), "EM")
		self.assertEqual(timesheets.person("Dr. Anna Beispiel", "", Person.INITIALS), "AB")
		self.assertEqual(timesheets.person("Hans-Peter Muster", "", Person.INITIALS), "HPM")
		self.assertEqual(timesheets.person("Erika Mustermann", "Beraterin", Person.ROLE), "Beraterin")
		self.assertEqual(timesheets.person("Erika Mustermann", "", Person.ROLE), "")
		self.assertEqual(timesheets.person("Erika Mustermann", "Beraterin", Person.NONE), "")
		self.assertEqual(timesheets.person("", "", Person.INITIALS), "")

	def test_a_way_of_naming_is_read_from_its_name_and_none_is_by_name(self):
		self.assertIs(timesheets.person_mode("Initials"), Person.INITIALS)
		self.assertIs(timesheets.person_mode(None), Person.NAME)
		with self.assertRaises(ValueError):
			timesheets.person_mode("Spitzname")


class OrderTest(TestCase):
	def test_the_entries_run_by_day_then_person_then_project(self):
		self.assertEqual(
			[(e.day.day, e.person, e.project) for e in timesheets.ordered(ENTRIES)],
			[
				(3, "Erika Mustermann", "Einführung"),
				(3, "Max Mustermann", "Einführung"),
				(5, "Erika Mustermann", "Datenmigration"),
				(12, "Max Mustermann", "Datenmigration"),
			],
		)


class SumTest(TestCase):
	def test_the_hours_add_up_in_total_and_per_project_and_person(self):
		self.assertEqual(timesheets.total(ENTRIES), D("17.75"))
		self.assertEqual(
			timesheets.subtotals(ENTRIES, "project"),
			[("Datenmigration", D("5.5")), ("Einführung", D("12.25"))],
		)
		self.assertEqual(
			timesheets.subtotals(ENTRIES, "person"),
			[("Erika Mustermann", D("10")), ("Max Mustermann", D("7.75"))],
		)

	def test_entries_without_a_project_or_person_add_up_under_an_empty_label(self):
		self.assertEqual(timesheets.subtotals([entry(1, "", "", "1")], "person"), [("", D(1))])


class ReconcileTest(TestCase):
	def test_the_hours_of_the_annex_equal_the_quantity_billed(self):
		"""The annex proves what the invoice bills: its hours are the quantity of the positions billed by time."""
		self.assertEqual(timesheets.reconcile(D("17.75"), [D("12.25"), D("5.5")]), (True, D("17.75")))
		self.assertEqual(timesheets.reconcile(D("17.75"), [D("12.25")]), (False, D("12.25")))
		self.assertEqual(timesheets.reconcile(D("17.75"), []), (False, D(0)))

	def test_a_difference_below_a_hundredth_of_an_hour_counts_as_none(self):
		self.assertEqual(timesheets.reconcile(D("17.751"), [D("17.75")]), (True, D("17.75")))


class PlacementTest(TestCase):
	def test_the_annex_goes_with_the_invoice_alone_or_not_at_all(self):
		self.assertIs(timesheets.placement("Separate document"), timesheets.Placement.SEPARATE)
		self.assertIs(timesheets.placement(None), timesheets.Placement.WITH_INVOICE)
		self.assertIs(timesheets.placement("Not printed"), timesheets.Placement.NONE)
