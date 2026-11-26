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


FORMATS = ROOT / "briefbote" / "briefbote" / "print_format"
# The print formats documented on the page of another: the Quittung with the Zahlungsbestätigung; and the page of a
# print format whose name has a hyphen, which its folder writes with an underscore.
DOCS_PAGE = {"quittung": "zahlungsbestaetigung", "proforma_rechnung": "proforma-rechnung"}


def ascii_name(name: str) -> str:
	return name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


class ExamplesTest(TestCase):
	"""Every print format shows an example printed by briefbote/tests/print_examples.py, in the README and at the top
	of its page in the docs."""

	def test_every_print_format_has_an_example_in_the_readme_and_on_its_page(self):
		readme = (ROOT / "README.md").read_text(encoding="utf-8")
		formats = [path.name for path in FORMATS.iterdir() if (path / f"{path.name}.json").exists()]
		self.assertTrue(formats)
		for folder in formats:
			name = ascii_name(folder)
			with self.subTest(print_format=folder):
				self.assertTrue((ROOT / "docs" / "bilder" / "beispiele" / f"{name}.png").exists())
				self.assertTrue((ROOT / "docs" / "beispiele" / f"{name}.pdf").exists())
				self.assertIn(f'src="docs/bilder/beispiele/{name}.png"', readme)
				self.assertIn(f'href="docs/beispiele/{name}.pdf"', readme)
				page = (ROOT / "docs" / f"{DOCS_PAGE.get(name, name)}.md").read_text(encoding="utf-8")
				head = page.split("\n## ", 1)[0]
				self.assertIn(f"bilder/beispiele/{name}.png", head)

	def test_every_example_is_shown_in_the_readme(self):
		readme = (ROOT / "README.md").read_text(encoding="utf-8")
		for picture in (ROOT / "docs" / "bilder" / "beispiele").glob("*.png"):
			with self.subTest(example=picture.name):
				self.assertIn(f'src="docs/bilder/beispiele/{picture.name}"', readme)
				self.assertTrue((ROOT / "docs" / "beispiele" / f"{picture.stem}.pdf").exists())
