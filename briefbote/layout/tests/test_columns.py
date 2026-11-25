from decimal import Decimal
from unittest import TestCase

from briefbote.layout import columns, metrics
from briefbote.layout.columns import Cell

D = Decimal
BODY = D("9.5")
HEAD = D(8)


class ColumnsTest(TestCase):
	def test_a_column_takes_its_widest_cell_rounded_up_to_half_a_millimetre(self):
		width = columns.need([Cell("1.234,50 €", BODY), Cell("9,00 €", BODY)])
		self.assertGreaterEqual(width, metrics.width("1.234,50 €", BODY))
		self.assertLess(width - metrics.width("1.234,50 €", BODY), D("0.5"))
		self.assertEqual(width % D("0.5"), 0)

	def test_a_semibold_cell_needs_more_room(self):
		self.assertGreater(columns.need([Cell("Betrag", HEAD, True)]), columns.need([Cell("Betrag", HEAD)]))

	def test_an_empty_column_needs_nothing(self):
		self.assertEqual(columns.need([]), 0)

	def test_the_description_takes_what_the_figures_leave(self):
		found = columns.widths(
			D(165),
			{
				"quantity": [Cell("Menge", HEAD, True), Cell("8", BODY)],
				"amount": [
					Cell("Betrag", HEAD, True),
					Cell("960,00 €", BODY),
					Cell("123.456.789,00 €", D("10.5"), True),
				],
				"description": [],
			},
			{"quantity": D("2.4"), "amount": D("1.2")},
			"description",
		)
		self.assertEqual(sum(found.values()), D(165))
		self.assertGreater(found["amount"], metrics.width("123.456.789,00 €", BODY))
		self.assertGreater(found["description"], D(100))

	def test_a_column_that_may_wrap_stops_at_its_limit(self):
		head = {"project": [Cell("Einführung eines neuen Warenwirtschaftssystems", BODY)], "description": []}
		found = columns.widths(D(165), head, {"project": D("2.4")}, "description", limits={"project": D(40)})
		self.assertEqual(found, {"project": D(40), "description": D(125)})


class TotalsTest(TestCase):
	def test_the_totals_start_with_the_quantity_where_their_labels_fit(self):
		labels = [Cell("Nettobetrag", BODY, True), Cell("Gesamtbetrag", D("10.5"), True)]
		blank, label, amount = columns.totals(
			D(165), D(100), D(20), labels, [Cell("960,00 €", BODY)], D(2), D(3)
		)
		self.assertEqual((blank, label + amount), (D(100), D(65)))
		self.assertEqual(amount, D(20))

	def test_a_long_label_or_a_large_total_starts_them_further_left(self):
		labels = [Cell("Umsatzsteuer 19 % auf 123.456.789,00 €", BODY)]
		amounts = [Cell("146.913.579,00 €", D("10.5"), True)]
		blank, label, amount = columns.totals(D(165), D(110), D(20), labels, amounts, D(2), D(3))
		self.assertEqual(amount, columns.need(amounts) + D(3))
		self.assertEqual(label, columns.need(labels) + D(2))
		self.assertEqual(blank + label + amount, D(165))
		self.assertLess(blank, D(110))
