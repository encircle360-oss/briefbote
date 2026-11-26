"""The weight of the totals, read from the stylesheet without a bench: only the line of what a document comes to is
bold; the net amount and the tax lines are regular, so that the eye goes to the total."""

import re
from pathlib import Path
from unittest import TestCase

STYLE = Path(__file__).resolve().parents[1] / "templates" / "includes" / "briefbote" / "style.html"


class TotalsWeightTest(TestCase):
	def test_only_the_total_of_the_totals_is_bold(self):
		style = STYLE.read_text(encoding="utf-8")
		bold = re.findall(r"([^{}]*)\{[^{}]*font-weight:\s*600[^{}]*\}", style)
		selectors = " ".join(bold)
		self.assertIn("tr.bb-total td", selectors)
		self.assertNotIn("tr.bb-sum td", selectors)
