"""Where a printout goes, which decides what the stylesheet adds.

Frappe 16 renders a print format on three ways (frappe/printing/page/print/print.js, frappe/www/printview.py):
through a PDF generator, as for the button PDF, a download, an e-mail attachment or a bulk print; as the preview of
the print view on the screen (get_html_and_style); and as the page /printview, which the browser prints itself. Only
a generator fills the page numbers of the running foot and repeats it on every page. The browser gets a page line
from the margin boxes of @page instead, with counters for page and pages; the screen gets none.
"""

PDF = "pdf"
SCREEN = "screen"
BROWSER = "browser"
PREVIEW = "frappe.www.printview.get_html_and_style"


def medium(path: str | None) -> str:
	"""The medium of a printout by the path of the request that renders it."""
	if not path:
		return PDF
	if path.rstrip("/").endswith(PREVIEW):
		return SCREEN
	if path.rstrip("/") == "/printview":
		return BROWSER
	return PDF


def _css(text: str) -> str:
	"""A text as the content of a CSS string, with every character that could end it escaped."""
	escaped = "".join(f"\\{ord(char):X} " if char in '"\\\n\r·' else char for char in text)
	return f'"{escaped}"'


def page_counter(title: str, label: str) -> str:
	"""The CSS content of the page line of a browser printout: the title, a dot, and the label of the language with
	counter(page) for {0} and counter(pages) for {1}."""
	before, _, after = label.partition("{0}")
	middle, _, rest = after.partition("{1}")
	prefix = _css(f"{title} · {before}")
	if "{1}" not in after:
		return f"{prefix} counter(page) {_css(after)}"
	return f"{prefix} counter(page) {_css(middle)} counter(pages){' ' + _css(rest) if rest else ''}"
