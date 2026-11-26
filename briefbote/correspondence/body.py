"""The text of a business letter, as the rich text editor of Frappe or a word processor wrote it, in the typography of
the letter.

The text comes from the owner of the letter rendered already (content_preview of a Business Letter); it is read as
HTML and never as a template. What prints is a fixed set of blocks the stylesheet knows: paragraphs, empty lines,
headings, lists with their marks and numbers, simple tables, images as data URLs. Bold, italic, underline, strike,
sub- and superscript keep their meaning; fonts, sizes, colours, styles, classes and every other attribute of the
content are dropped, so that a letter pasted from a word processor prints like any other. A link prints its text and
where it leads. Scripts, styles and embedded frames are dropped with their content. An image prints only where the
resolver gives it as a data URL of a raster image: a printout loads nothing (AGENTS.md).

Paragraphs are separated by a blank line (DIN 5008, docs/geschaeftsbrief-format.md); the stylesheet sets that space.
A long letter breaks between blocks: a heading stays with what follows it, and the last lines of the letter, its
closing and signature, stay with the text before them, so that no page ends with a heading or holds the closing
alone.
"""

import html
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from html.parser import HTMLParser

type Resolver = Callable[[str], str | None]

# Elements dropped with all they hold: they carry code, styles or embedded content, never text of the letter.
DROPPED = frozenset(
	{
		"script",
		"style",
		"head",
		"title",
		"iframe",
		"object",
		"embed",
		"template",
		"svg",
		"math",
		"noscript",
		"xml",
		"video",
		"audio",
		"canvas",
		"select",
		"textarea",
		"button",
	}
)
VOID = frozenset(
	{"br", "img", "hr", "meta", "link", "input", "col", "wbr", "area", "base", "source", "param", "track"}
)
HEADINGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
LISTS = frozenset({"ul", "ol"})
# Elements that stand as a block of their own; any other element runs on in the line.
BLOCK_TAGS = frozenset(
	{
		"p",
		"blockquote",
		"pre",
		"table",
		"hr",
		"li",
		"div",
		"section",
		"article",
		"header",
		"footer",
		"main",
		"aside",
		"nav",
		"figure",
		"figcaption",
		"address",
		"dl",
		"dt",
		"dd",
		"center",
		"html",
		"body",
		"form",
		"fieldset",
		"thead",
		"tbody",
		"tfoot",
		"tr",
		"td",
		"th",
	}
	| HEADINGS
	| LISTS
)
INLINE = {
	"b": "strong",
	"strong": "strong",
	"i": "em",
	"em": "em",
	"u": "u",
	"ins": "u",
	"s": "s",
	"strike": "s",
	"del": "s",
	"sub": "sub",
	"sup": "sup",
}
ALIGNMENTS = {"ql-align-center": "bb-align-center", "ql-align-right": "bb-align-right"}
INDENT = re.compile(r"ql-indent-(\d+)")
MOST_INDENT = 4
# Levels of a list: deeper items print at the last level.
MOST_LEVEL = 3
BULLETS = ("•", "\u2013", "·")
IMAGE = re.compile(r"data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/=]+")
WIDEST_IMAGE = 2000
MOST_SPAN = 20
SPACES = re.compile(r"[ \t\n\r\f]+")
# A line of bold text this long or shorter reads as a heading.
HEADING_LENGTH = 60
# About as many characters as a line of the text holds: 175 mm of Inter at 9.5 pt.
CHARACTERS_PER_LINE = 95
# The closing of a letter and the lines before it that stay on one page, in lines of text.
CLOSING_LINES = 8
KEEP = '<div class="bb-keep">{0}</div>'


@dataclass
class Node:
	tag: str
	attrs: dict[str, str] = field(default_factory=dict)
	children: list[Node | str] = field(default_factory=list)

	def classes(self) -> list[str]:
		return self.attrs.get("class", "").split()


class _Reader(HTMLParser):
	"""The content as a tree, forgiving as a browser: an end tag without its start is ignored, an open element ends
	with the content, and comments, declarations and processing instructions are dropped."""

	def __init__(self):
		super().__init__(convert_charrefs=True)
		self.root = Node("root")
		self.stack = [self.root]
		self.skipping: list[str] = []

	def handle_starttag(self, tag, attrs):
		if self.skipping:
			if tag not in VOID:
				self.skipping.append(tag)
			return
		if tag in DROPPED:
			self.skipping = [tag]
			return
		node = Node(tag, {key: value or "" for key, value in attrs})
		self.stack[-1].children.append(node)
		if tag not in VOID:
			self.stack.append(node)

	def handle_endtag(self, tag):
		if self.skipping:
			if tag in self.skipping:
				del self.skipping[len(self.skipping) - 1 - self.skipping[::-1].index(tag) :]
			return
		tags = [node.tag for node in self.stack[1:]]
		if tag in tags:
			del self.stack[len(tags) - tags[::-1].index(tag) :]

	def handle_data(self, data):
		if not self.skipping:
			self.stack[-1].children.append(data)


def _tree(content: str) -> Node:
	reader = _Reader()
	reader.feed(content)
	reader.close()
	return reader.root


@dataclass(frozen=True, slots=True)
class Block:
	"""One block of the letter: paragraph, blank, heading, list or table, its HTML and its text."""

	kind: str
	html: str
	text: str
	lines: int = 1


@dataclass(frozen=True, slots=True)
class Body:
	blocks: tuple[Block, ...]
	html: str
	empty: bool


def _has_block(node: Node) -> bool:
	return any(
		isinstance(child, Node) and (child.tag in BLOCK_TAGS or _has_block(child)) for child in node.children
	)


def _plain(markup: str) -> str:
	return html.unescape(re.sub(r"<[^>]+>", "", markup)).replace("\u00a0", " ").strip()


def _tidy(markup: str) -> str:
	markup = re.sub(r" {2,}", " ", markup)
	markup = re.sub(r" ?<br> ?", "<br>", markup)
	markup = markup.strip(" ")
	while markup.startswith("<br>"):
		markup = markup[4:]
	while markup.endswith("<br>"):
		markup = markup[:-4]
	return markup


def _visible(markup: str) -> bool:
	return bool(_plain(markup)) or "<img " in markup


def roman(number: int) -> str:
	"""The number in small roman numerals, as the third level of a numbered list counts."""
	numerals = (
		(1000, "m"),
		(900, "cm"),
		(500, "d"),
		(400, "cd"),
		(100, "c"),
		(90, "xc"),
		(50, "l"),
		(40, "xl"),
		(10, "x"),
		(9, "ix"),
		(5, "v"),
		(4, "iv"),
		(1, "i"),
	)
	found = ""
	for value, letters in numerals:
		while number >= value:
			found += letters
			number -= value
	return found


def _alphabetic(number: int) -> str:
	letters = ""
	while number:
		number, rest = divmod(number - 1, 26)
		letters = chr(ord("a") + rest) + letters
	return letters


def _ordinal(level: int, number: int) -> str:
	return (f"{number}.", f"{_alphabetic(number)})", f"{roman(number)}.")[level % 3]


class _Writer:
	def __init__(self, image: Resolver):
		self.image = image
		self.blocks: list[Block] = []

	# The text of a block, with the markup the letter keeps.

	def inline(self, nodes, pre: bool = False, cell: bool = False) -> str:
		parts = []
		for node in nodes:
			if isinstance(node, str):
				if pre:
					parts.append(
						"<br>".join(
							html.escape(SPACES.sub(" ", line), quote=False) for line in node.split("\n")
						)
					)
				else:
					parts.append(html.escape(SPACES.sub(" ", node), quote=False))
			elif cell and node.tag in BLOCK_TAGS:
				parts.append(f"<br>{self.inline(node.children, cell=True)}<br>")
			else:
				parts.append(self.element(node, pre, cell))
		return _tidy("".join(parts)) if not pre else "".join(parts)

	def element(self, node: Node, pre: bool, cell: bool) -> str:
		if node.tag == "br":
			return "<br>"
		if node.tag == "img":
			return self.picture(node)
		if node.tag == "span" and "ql-ui" in node.classes():
			return ""
		inner = self.inline(node.children, pre, cell)
		if node.tag in INLINE:
			tag = INLINE[node.tag]
			return f"<{tag}>{inner}</{tag}>" if inner.strip() else inner
		if node.tag == "a":
			return inner + self.target(node, inner)
		return inner

	def target(self, node: Node, inner: str) -> str:
		href = node.attrs.get("href", "").strip()
		if href.lower().startswith("mailto:"):
			shown = href[len("mailto:") :].split("?")[0]
		elif re.match(r"https?://", href, re.IGNORECASE):
			shown = href
		else:
			return ""
		text = _plain(inner)
		if text in (shown, href):
			return ""
		escaped = html.escape(shown, quote=False)
		return f" ({escaped})" if text else escaped

	def picture(self, node: Node) -> str:
		source = node.attrs.get("src", "").strip()
		found = self.image(source) if source else None
		if not found or not IMAGE.fullmatch(found):
			return ""
		width = node.attrs.get("width", "")
		style = (
			f' style="width: {int(width)}px;"' if width.isdigit() and 0 < int(width) <= WIDEST_IMAGE else ""
		)
		return f'<img class="bb-image" src="{found}" alt=""{style}>'

	# The blocks.

	def add(self, kind: str, markup: str, text: str, lines: int = 1) -> None:
		self.blocks.append(Block(kind, markup, text, lines))

	def classes(self, node: Node | None, indent: int = 0) -> str:
		names = node.classes() if node else []
		found = [ALIGNMENTS[name] for name in names if name in ALIGNMENTS]
		for name in names:
			if match := INDENT.fullmatch(name):
				indent += int(match.group(1))
		if indent:
			found.append(f"bb-indent-{min(indent, MOST_INDENT)}")
		return f' class="{" ".join(found)}"' if found else ""

	def paragraph(self, nodes, node: Node | None = None, indent: int = 0, pre: bool = False) -> None:
		markup = self.inline(nodes, pre=pre)
		if pre:
			markup = _tidy(markup)
		if not _visible(markup):
			self.add("blank", '<p class="bb-blank"></p>', "", 1)
			return
		text = _plain(markup)
		kind = "paragraph"
		if re.fullmatch(r"<strong>(?:(?!</strong>).)*</strong>", markup) and len(text) <= HEADING_LENGTH:
			kind = "heading"
		lines = max(1, math.ceil(len(text) / CHARACTERS_PER_LINE))
		self.add(kind, f"<p{self.classes(node, indent)}>{markup}</p>", text, lines)

	def heading(self, node: Node) -> None:
		markup = self.inline(node.children)
		if _visible(markup):
			self.add("heading", f'<div class="bb-heading">{markup}</div>', _plain(markup))

	def items(self, node: Node, depth: int, found: list[tuple[str, int, str]]) -> None:
		for child in node.children:
			if not isinstance(child, Node) or child.tag != "li":
				continue
			kind = child.attrs.get("data-list") or ("ordered" if node.tag == "ol" else "bullet")
			extra = sum(int(match.group(1)) for name in child.classes() if (match := INDENT.fullmatch(name)))
			markup = self.inline(
				[part for part in child.children if not (isinstance(part, Node) and part.tag in LISTS)]
			)
			if _visible(markup):
				found.append(
					("ordered" if kind == "ordered" else "bullet", min(depth + extra, MOST_LEVEL), markup)
				)
			for part in child.children:
				if isinstance(part, Node) and part.tag in LISTS:
					self.items(part, depth + 1, found)

	def listing(self, node: Node) -> None:
		found: list[tuple[str, int, str]] = []
		self.items(node, 0, found)
		if not found:
			return
		counters: dict[int, int] = {}
		rows = []
		for kind, level, markup in found:
			counters = {key: value for key, value in counters.items() if key <= level}
			if kind == "ordered":
				counters[level] = counters.get(level, 0) + 1
				mark = _ordinal(level, counters[level])
			else:
				mark = BULLETS[level % len(BULLETS)]
			rows.append(
				f'<div class="bb-li bb-level-{level}"><span class="bb-li-mark">{mark}</span>{markup}</div>'
			)
		text = " ".join(_plain(markup) for _kind, _level, markup in found)
		lines = sum(max(1, math.ceil(len(_plain(markup)) / CHARACTERS_PER_LINE)) for _k, _l, markup in found)
		self.add("list", f'<div class="bb-list">{"".join(rows)}</div>', text, lines)

	def cell(self, node: Node) -> str:
		attributes = ""
		for name in ("colspan", "rowspan"):
			value = node.attrs.get(name, "")
			if value.isdigit() and 1 < int(value) <= MOST_SPAN:
				attributes += f' {name}="{int(value)}"'
		markup = _tidy(self.inline(node.children, cell=True).replace("<br><br>", "<br>"))
		return f"<{node.tag}{attributes}>{markup}</{node.tag}>"

	def table(self, node: Node) -> None:
		head, rows = [], []

		def collect(parent: Node, into: list[str]) -> None:
			for child in parent.children:
				if not isinstance(child, Node):
					continue
				if child.tag == "tr":
					cells = [
						self.cell(part)
						for part in child.children
						if isinstance(part, Node) and part.tag in ("td", "th")
					]
					if cells:
						into.append(f"<tr>{''.join(cells)}</tr>")
				elif child.tag == "thead":
					collect(child, head)
				elif child.tag in ("tbody", "tfoot"):
					collect(child, into)

		collect(node, rows)
		if not rows and not head:
			return
		markup = '<table class="bb-text-table">'
		if head:
			markup += f"<thead>{''.join(head)}</thead>"
		markup += f"<tbody>{''.join(rows)}</tbody></table>"
		self.add("table", markup, _plain(markup), len(head) + len(rows))

	def walk(self, nodes) -> None:
		buffer: list[Node | str] = []

		def flush() -> None:
			if any(isinstance(part, Node) or part.strip(" \t\n\r\f") for part in buffer):
				self.paragraph(list(buffer))
			buffer.clear()

		for node in nodes:
			if isinstance(node, str):
				buffer.append(node)
				continue
			if node.tag in ("p", "hr", "blockquote", "pre", "table") or node.tag in HEADINGS | LISTS:
				flush()
				if node.tag == "p":
					self.paragraph(node.children, node)
				elif node.tag in HEADINGS:
					self.heading(node)
				elif node.tag in LISTS:
					self.listing(node)
				elif node.tag == "table":
					self.table(node)
				elif node.tag == "blockquote":
					self.paragraph(node.children, node, indent=1)
				elif node.tag == "pre":
					self.paragraph(node.children, node, pre=True)
			elif _has_block(node):
				flush()
				self.walk(node.children)
			elif node.tag in BLOCK_TAGS:
				flush()
				self.paragraph(node.children, node)
			else:
				buffer.append(node)
		flush()


def blocks(content: str | None, image: Resolver) -> list[Block]:
	"""The blocks of the text, without blank lines at its start and end."""
	writer = _Writer(image)
	writer.walk(_tree(content or "").children)
	found = writer.blocks
	while found and found[0].kind == "blank":
		found.pop(0)
	while found and found[-1].kind == "blank":
		found.pop()
	return found


def _closing(found: list[Block]) -> int:
	"""Where the group of the last lines begins: the last blocks of the letter up to CLOSING_LINES lines, with the
	paragraph before them where they are only short lines, and with a heading right before them; no group where the
	letter ends in a list or table, and no table in the group."""
	if not found or found[-1].kind in ("list", "table"):
		return len(found)
	start, lines = len(found), 0
	while start > 0 and found[start - 1].kind != "table" and lines + found[start - 1].lines <= CLOSING_LINES:
		start -= 1
		lines += found[start].lines
	group = found[start:]
	short = all(block.kind in ("paragraph", "blank", "heading") and block.lines == 1 for block in group)
	if short and start > 0 and found[start - 1].kind in ("paragraph", "heading"):
		start -= 1
	before = start
	while before > 0 and found[before - 1].kind == "blank":
		before -= 1
	if before > 0 and found[before - 1].kind == "heading":
		start = before - 1
	return start


def arrange(found: list[Block]) -> str:
	"""The HTML of the blocks, with each heading kept with what follows it and the closing with the text before."""
	closing = _closing(found)
	parts, index = [], 0
	while index < closing:
		block = found[index]
		if block.kind != "heading":
			parts.append(block.html)
			index += 1
			continue
		end = index + 1
		while end < closing and found[end].kind == "blank":
			end += 1
		end = min(end + 1, closing)
		parts.append(KEEP.format("\n".join(part.html for part in found[index:end])))
		index = end
	if closing < len(found):
		parts.append(KEEP.format("\n".join(block.html for block in found[closing:])))
	return "\n".join(parts)


def render(content: str | None, image: Resolver) -> Body:
	"""The text of the letter in its typography, and whether it holds anything to read."""
	found = blocks(content, image)
	return Body(tuple(found), arrange(found), not any(block.kind != "blank" for block in found))
