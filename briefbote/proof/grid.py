"""Checks of a printout that measure where its words stand against each other: an amount that ends where the column it
sums ends, a text that never breaks over two lines, the distance of the head of a table from the line above, and the
darkness of a line that must be seen. The module imports no Frappe; the proof in CI reads the words with
`pdftotext -bbox` and the pixels with `pdftoppm -gray`.
"""

from briefbote.proof.pages import MM, Page, Word, lines, text_of
from briefbote.proof.raster import INCH_MM, Area, Raster

# How far in points the right edge of an amount may lie from that of its column.
TOLERANCE = 1.0


def aligned(pages: list[Page], head: str, label: str) -> list[str]:
	"""The last word of every line that starts with the label ends where the column head of that page ends."""
	problems = []
	for number, page in enumerate(pages, start=1):
		heads = [word for word in page.words if word.text == head]
		if not heads:
			continue
		edge = max(word.x1 for word in heads)
		for line in lines(page.words):
			if text_of(line).startswith(label) and abs(line[-1].x1 - edge) > TOLERANCE:
				problems.append(
					f"Seite {number}: „{label}“ endet bei {line[-1].x1:.1f} pt, die Spalte „{head}“ bei {edge:.1f} pt"
				)
	return problems


def on_one_line(pages: list[Page], texts) -> list[str]:
	"""Each text stands whole on one line of some page."""
	every = [text_of(line) for page in pages for line in lines(page.words)]
	return [
		f"„{text}“ steht auf keiner Zeile ganz" for text in texts if not any(text in line for line in every)
	]


def space_above(pages: list[Page], head: str, minimum: float) -> list[str]:
	"""The line that is the head of a table stands at least minimum millimetres below the line above it, on the
	first page that has the head below another line."""
	for page in pages:
		found = lines(page.words)
		for index, line in enumerate(found):
			if text_of(line) == head and index:
				gap = (min(word.y0 for word in line) - max(word.y1 for word in found[index - 1])) / MM
				if gap < minimum:
					text = f"{gap:.1f}".replace(".", ",")
					return [f"„{head}“ steht {text} mm unter der Zeile darüber, mindestens {minimum:g} mm"]
				return []
	return []


def darkest(raster: Raster, within: Area) -> int:
	"""The grey of the darkest pixel within the area, 255 where it lies off the image."""
	scale = raster.dpi / INCH_MM
	left, top = max(int(within.left * scale), 0), max(int(within.top * scale), 0)
	right, bottom = (
		min(int(within.right * scale), raster.width),
		min(int(within.bottom * scale), raster.height),
	)
	values = [
		value
		for y in range(top, bottom)
		for value in raster.pixels[y * raster.width + left : y * raster.width + right]
	]
	return min(values, default=255)


def above(word: Word, height: float) -> Area:
	"""The band of the given height in millimetres right above a word and as wide as it."""
	return Area(word.x0 / MM, word.y0 / MM - height, word.x1 / MM, word.y0 / MM)
