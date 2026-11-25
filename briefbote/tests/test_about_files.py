"""Über Briefbote, read from the files without a bench: the block that says who makes Briefbote and where its source,
documentation and issues are."""

import csv
import re
from html.parser import HTMLParser
from pathlib import Path
from unittest import TestCase

from briefbote import __version__
from briefbote.briefbote import about

APP = Path(__file__).resolve().parents[1]
TRANSLATIONS = APP / "translations" / "de.csv"
REPOSITORY = "https://github.com/encircle360-oss/briefbote"
# What the block shows in German, word for word, and where its links lead.
GERMAN = {
	"title": f"Briefbote {__version__}",
	"licence": "Briefbote ist freie Software (AGPL-3.0) der encircle360 GmbH und aller Mitwirkenden.",
	"disclaimer": "Ohne Gewähr. Briefbote ersetzt keine rechtliche oder steuerliche Beratung.",
	"services": "Einführung, Betrieb und Unterstützung: encircle360.com",
}
LINKS = [
	("Quelltext", REPOSITORY),
	("Dokumentation", f"{REPOSITORY}/tree/main/docs"),
	("Fehler melden", f"{REPOSITORY}/issues"),
	("Haftungsausschluss", f"{REPOSITORY}/blob/main/docs/haftungsausschluss.md"),
	("encircle360.com", "https://encircle360.com/?ref=briefbote"),
]


def translations() -> dict[str, str]:
	with TRANSLATIONS.open(encoding="utf-8", newline="") as file:
		return dict(csv.reader(file))


def german(text: str) -> str:
	return translations().get(text, text)


class Markup(HTMLParser):
	"""The elements of a piece of HTML with their attributes, the links with their text, and the text."""

	def __init__(self, markup: str):
		super().__init__()
		self.elements: list[tuple[str, dict[str, str | None]]] = []
		self.links: list[tuple[str, dict[str, str | None]]] = []
		self.text: list[str] = []
		self._link: dict[str, str | None] | None = None
		self._link_text: list[str] = []
		self.feed(markup)

	def handle_starttag(self, tag, attrs):
		self.elements.append((tag, dict(attrs)))
		if tag == "a":
			self._link, self._link_text = dict(attrs), []

	def handle_endtag(self, tag):
		if tag == "a" and self._link is not None:
			self.links.append(("".join(self._link_text).strip(), self._link))
			self._link = None

	def handle_data(self, data):
		self.text.append(data)
		if self._link is not None:
			self._link_text.append(data)

	def lines(self) -> list[str]:
		return [line for line in (re.sub(r"\s+", " ", part).strip() for part in self.text) if line]


def remote(markup: str) -> list[str]:
	"""Whatever in a piece of HTML would make the browser load something by itself rather than on a click."""
	found = re.findall(r"<\s*(?:script|link|iframe|object|embed|video|audio|source)\b", markup, re.IGNORECASE)
	found += re.findall(r"url\(|@import|srcset", markup, re.IGNORECASE)
	parsed = Markup(markup)
	found += [
		value or ""
		for tag, attributes in parsed.elements
		for name, value in attributes.items()
		if name in {"src", "poster", "data"} and not (value or "").startswith("/assets/briefbote/")
	]
	found += [
		attributes.get("href") or ""
		for tag, attributes in parsed.elements
		if tag != "a" and "href" in attributes
	]
	return found


class AboutBlockTest(TestCase):
	def setUp(self):
		self.markup = about.render(german)
		self.parsed = Markup(self.markup)

	def test_shows_the_logo_the_version_the_licence_and_the_links_in_german(self):
		self.assertIn(
			("img", "/assets/briefbote/images/briefbote-logo.svg"),
			[(tag, attributes.get("src")) for tag, attributes in self.parsed.elements],
		)
		lines = " ".join(self.parsed.lines())
		for part, text in GERMAN.items():
			with self.subTest(part=part):
				self.assertIn(text, lines)
		self.assertEqual([(text, attributes["href"]) for text, attributes in self.parsed.links], LINKS)

	def test_the_logo_is_part_of_the_app(self):
		self.assertTrue((APP / "public" / about.LOGO.removeprefix("/assets/briefbote/")).is_file())

	def test_shows_the_version_it_is_given_and_by_default_the_installed_one(self):
		self.assertIn(f"Briefbote {__version__}", " ".join(Markup(about.render(str)).lines()))
		self.assertIn("Briefbote 99.1.0", " ".join(Markup(about.render(str, "99.1.0")).lines()))
		self.assertIn("Briefbote 1&lt;2", about.render(str, "1<2"))

	def test_the_pages_it_links_in_the_repository_exist(self):
		for text, attributes in self.parsed.links:
			path = (attributes.get("href") or "").removeprefix(f"{REPOSITORY}/").split("/", 2)
			if path[0] in {"blob", "tree"}:
				with self.subTest(link=text):
					self.assertTrue((APP.parent / path[2]).exists())

	def test_every_link_opens_in_a_new_tab_without_telling_where_it_came_from(self):
		for text, attributes in self.parsed.links:
			with self.subTest(link=text):
				self.assertEqual(attributes.get("target"), "_blank")
				self.assertEqual(set((attributes.get("rel") or "").split()), {"noopener", "noreferrer"})

	def test_loads_nothing_from_another_site(self):
		self.assertEqual(remote(self.markup), [])

	def test_follows_the_colours_of_the_desk_in_light_and_dark(self):
		"""No colour of its own: the variables of the desk, which its dark theme sets anew."""
		self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|\b(?:white|black)\b", self.markup), [])
		for variable in ("--border-color", "--card-bg", "--text-color"):
			with self.subTest(variable=variable):
				self.assertIn(f"var({variable}", self.markup)

	def test_wraps_on_a_narrow_screen(self):
		(section,) = [attributes for tag, attributes in self.parsed.elements if tag == "section"]
		self.assertIn("flex-wrap: wrap", section["style"] or "")
		self.assertIn("min-width: 0", self.markup)

	def test_escapes_what_a_translation_brings(self):
		markup = about.render(lambda text: f"<b>{text}</b>")
		self.assertNotIn("<b>", markup)

	def test_every_text_reads_in_german(self):
		self.assertEqual(sorted(set(about.TEXTS) - translations().keys()), [])
		self.assertEqual(german("About Briefbote"), about.BLOCK)
