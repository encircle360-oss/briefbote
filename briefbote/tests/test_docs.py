"""The documentation, read without a bench: every link between its pages leads to a page and a heading that exist."""

import re
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[2]
PAGES = [
	ROOT / "README.md",
	ROOT / "AGENTS.md",
	ROOT / "CONTRIBUTING.md",
	ROOT / "SECURITY.md",
	*(ROOT / "docs").glob("*.md"),
]
LINK = re.compile(r"\]\((?!https?://|mailto:)([^)#\s]*)(?:#([^)\s]+))?\)")
HEADING = re.compile(r"^#+\s+(.+)$", re.MULTILINE)


def anchor(heading: str) -> str:
	"""The anchor GitHub gives a heading: lower case, without punctuation, spaces as hyphens."""
	text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
	return text.replace(" ", "-")


class LinksTest(TestCase):
	def test_every_link_leads_to_a_page_and_heading_that_exist(self):
		for page in PAGES:
			for target, fragment in LINK.findall(page.read_text(encoding="utf-8")):
				with self.subTest(page=page.name, link=f"{target}#{fragment}"):
					path = (page.parent / target).resolve() if target else page
					self.assertTrue(path.exists())
					if fragment and path.suffix == ".md":
						headings = {anchor(h) for h in HEADING.findall(path.read_text(encoding="utf-8"))}
						self.assertIn(fragment, headings)

	def test_every_page_of_the_docs_is_linked_from_the_readme(self):
		readme = (ROOT / "README.md").read_text(encoding="utf-8")
		for page in (ROOT / "docs").glob("*.md"):
			with self.subTest(page=page.name):
				self.assertIn(f"(docs/{page.name})", readme)
