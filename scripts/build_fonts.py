"""Build the fonts of the printouts from the release of Inter, checked by its SHA-256.

    python scripts/build_fonts.py Inter-4.1.zip

Inter is under the SIL Open Font License 1.1 and names no Reserved Font Name, so a subset may keep its name. The
subset holds the Latin letters of the languages of the EU, the punctuation and symbols of business documents and the
figures; its digits are the tabular ones of the feature tnum, so that amounts line up in their column with either PDF
generator, of which wkhtmltopdf knows no font features. It keeps kerning and the features that compose and localise
glyphs, but none that replaces a sequence of letters, so that „Nr.“ always prints as letters. The files land in
briefbote/public/fonts with the licence.
"""

import hashlib
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

RELEASE_SHA256 = "9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e"
WEIGHTS = {"Regular": "extras/ttf/Inter-Regular.ttf", "SemiBold": "extras/ttf/Inter-SemiBold.ttf"}
LICENCE = "LICENSE.txt"
TARGET = Path(__file__).resolve().parents[1] / "briefbote" / "public" / "fonts"
UNICODES = [
	*range(0x20, 0x7F),  # Basic Latin
	*range(0xA0, 0x180),  # Latin-1 Supplement, Latin Extended-A
	*range(0x218, 0x21C),  # Romanian S and T with comma below
	0x2009,
	0x200A,
	0x2011,
	0x202F,  # thin, hair, non-breaking hyphen, narrow no-break space
	*range(0x2010, 0x2027),  # dashes, quotation marks, bullet, ellipsis
	0x2030,
	0x2039,
	0x203A,
	0x20AC,
	0x2122,
	0x2212,
	0x2116,  # per mille, guillemets, euro, trade mark, minus, numero
]


def tabular_digits(font: TTFont) -> None:
	"""Map the digits to their glyphs of the feature tnum."""
	gsub = font["GSUB"].table
	lookups = {
		index
		for record in gsub.FeatureList.FeatureRecord
		if record.FeatureTag == "tnum"
		for index in record.Feature.LookupListIndex
	}
	substitutions = {}
	for index in sorted(lookups):
		for table in gsub.LookupList.Lookup[index].SubTable:
			substitutions.update(getattr(table, "mapping", {}))
	for cmap in font["cmap"].tables:
		for code in range(0x30, 0x3A):
			glyph = cmap.cmap.get(code)
			if glyph in substitutions:
				cmap.cmap[code] = substitutions[glyph]


def main(release: str) -> None:
	data = Path(release).read_bytes()
	if hashlib.sha256(data).hexdigest() != RELEASE_SHA256:
		raise SystemExit(f"{release} is not the release of Inter 4.1")
	TARGET.mkdir(parents=True, exist_ok=True)
	with zipfile.ZipFile(BytesIO(data)) as archive:
		(TARGET / "OFL.txt").write_bytes(archive.read(LICENCE))
		for weight, member in WEIGHTS.items():
			font = TTFont(BytesIO(archive.read(member)), recalcTimestamp=False)
			tabular_digits(font)
			options = subset.Options()
			options.layout_features = ["kern", "ccmp", "locl", "case"]
			options.name_IDs = ["*"]
			options.hinting = False
			options.notdef_outline = True
			subsetter = subset.Subsetter(options)
			subsetter.populate(unicodes=UNICODES)
			subsetter.subset(font)
			font.save(TARGET / f"Inter-{weight}.ttf")


if __name__ == "__main__":
	main(*sys.argv[1:])
