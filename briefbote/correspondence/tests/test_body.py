from unittest import TestCase

from briefbote.correspondence import body

PNG = "data:image/png;base64,iVBORw0KGgo="
# A paragraph of six lines and one of two.
LONG = "Ein Absatz, der über mehrere Zeilen läuft und so den Text eines Briefs vertritt. " * 7
TWO_LINES = (
	"Der letzte Absatz des Briefs, der etwas länger ist als eine Zeile des Textes und deshalb zwei braucht."
)


def no_images(_source: str) -> str | None:
	return None


def files(source: str) -> str | None:
	return PNG if source == "/files/logo.png" else None


def html(content: str, image=no_images) -> str:
	return body.render(content, image).html


def blocks(content: str, image=no_images) -> list[str]:
	return [block.html for block in body.blocks(content, image)]


class TextTest(TestCase):
	def test_a_paragraph_keeps_its_text_escaped(self):
		self.assertEqual(blocks("<p>Preis < 5 € & mehr</p>"), ["<p>Preis &lt; 5 € &amp; mehr</p>"])

	def test_the_wrapper_of_the_editor_is_no_block_of_its_own(self):
		self.assertEqual(
			blocks('<div class="ql-editor read-mode"><p>Eins</p><p>Zwei</p></div>'),
			["<p>Eins</p>", "<p>Zwei</p>"],
		)

	def test_text_outside_a_paragraph_becomes_one(self):
		self.assertEqual(
			blocks("Sehr geehrte Frau Muster,<br>vielen Dank."),
			["<p>Sehr geehrte Frau Muster,<br>vielen Dank.</p>"],
		)

	def test_bold_italic_underline_and_strike_keep_their_meaning(self):
		self.assertEqual(
			blocks(
				"<p><b>fett</b> <strong>fett</strong> <i>kursiv</i> <em>kursiv</em> <u>unten</u> <s>weg</s></p>"
			),
			[
				"<p><strong>fett</strong> <strong>fett</strong> <em>kursiv</em> <em>kursiv</em> <u>unten</u> <s>weg</s></p>"
			],
		)

	def test_an_empty_line_of_the_editor_stays_an_empty_line(self):
		self.assertEqual(
			blocks("<p>Gruß</p><p><br></p><p>Name</p>"),
			["<p>Gruß</p>", '<p class="bb-blank"></p>', "<p>Name</p>"],
		)

	def test_white_space_collapses_as_a_browser_would(self):
		self.assertEqual(blocks("<p>  viel \n\t Raum  </p>"), ["<p>viel Raum</p>"])

	def test_a_no_break_space_is_kept(self):
		self.assertEqual(blocks("<p>10\u00a0€</p>"), ["<p>10\u00a0€</p>"])

	def test_entities_are_read_and_written_again(self):
		self.assertEqual(blocks("<p>&quot;A&quot; &amp;&nbsp;B</p>"), ['<p>"A" &amp;\u00a0B</p>'])


class TypographyTest(TestCase):
	"""Whatever the editor or a word processor put in, the letter prints in its own font, size and colour."""

	def test_fonts_sizes_and_colours_are_dropped(self):
		self.assertEqual(
			blocks(
				'<p style="font-size:20pt;color:red"><font face="Comic Sans MS" color="#ff0000" size="7">laut</font>'
				' <span style="font-family: Times; background-color: yellow" class="ql-size-huge ql-font-serif">bunt</span></p>'
			),
			["<p>laut bunt</p>"],
		)

	def test_the_markup_of_a_word_processor_is_dropped(self):
		content = (
			"<!--[if gte mso 9]><xml><o:OfficeDocumentSettings></o:OfficeDocumentSettings></xml><![endif]-->"
			"<style>p.MsoNormal {margin:0cm; font-family:Calibri}</style>"
			'<p class="MsoNormal" style="mso-margin-top-alt:auto"><span lang="DE" style="mso-ansi-language:DE">'
			"Text<o:p></o:p></span></p>"
		)
		self.assertEqual(blocks(content), ["<p>Text</p>"])

	def test_scripts_and_embedded_frames_are_dropped_with_their_content(self):
		self.assertEqual(
			blocks("<p>A<script>alert(1)</script></p><iframe src='x'>B</iframe><object>C</object><p>D</p>"),
			["<p>A</p>", "<p>D</p>"],
		)

	def test_no_attribute_of_the_content_reaches_the_printout(self):
		self.assertEqual(
			blocks(
				'<p onclick="x()" id="a" data-x="1"><strong style="color:blue" onmouseover="y()">B</strong></p>'
			),
			["<p><strong>B</strong></p>"],
		)

	def test_an_alignment_of_the_editor_is_kept_and_justified_text_is_set_flush_left(self):
		self.assertEqual(
			blocks(
				'<p class="ql-align-center">Mitte</p><p class="ql-align-right">Rechts</p><p class="ql-align-justify">Block</p>'
			),
			['<p class="bb-align-center">Mitte</p>', '<p class="bb-align-right">Rechts</p>', "<p>Block</p>"],
		)

	def test_an_indent_of_the_editor_is_kept_up_to_four_steps(self):
		self.assertEqual(
			blocks(
				'<p class="ql-indent-2 ql-align-right">A</p><p class="ql-indent-7">B</p><p class="ql-indent-x">C</p>'
			),
			['<p class="bb-align-right bb-indent-2">A</p>', '<p class="bb-indent-4">B</p>', "<p>C</p>"],
		)

	def test_headings_of_every_level_print_as_one_heading(self):
		self.assertEqual(
			blocks("<h1>Eins</h1><h3 style='font-size:30px'>Drei</h3>"),
			['<div class="bb-heading">Eins</div>', '<div class="bb-heading">Drei</div>'],
		)

	def test_a_quotation_and_preformatted_text_print_as_paragraphs(self):
		self.assertEqual(
			blocks("<blockquote>Zitat</blockquote><pre>Zeile 1\nZeile 2</pre>"),
			['<p class="bb-indent-1">Zitat</p>', "<p>Zeile 1<br>Zeile 2</p>"],
		)

	def test_a_rule_prints_nothing(self):
		self.assertEqual(blocks("<p>A</p><hr><p>B</p>"), ["<p>A</p>", "<p>B</p>"])

	def test_a_block_inside_a_paragraph_runs_on_in_it(self):
		self.assertEqual(blocks("<p>A <div>B</div> C</p>"), ["<p>A B C</p>"])

	def test_sub_and_superscript_are_kept(self):
		self.assertEqual(
			blocks("<p>m<sup>2</sup> H<sub>2</sub>O</p>"), ["<p>m<sup>2</sup> H<sub>2</sub>O</p>"]
		)


class LinkTest(TestCase):
	def test_a_link_prints_its_text_and_where_it_leads_when_that_differs(self):
		self.assertEqual(
			blocks('<p><a href="https://example.com/agb">unsere AGB</a></p>'),
			["<p>unsere AGB (https://example.com/agb)</p>"],
		)

	def test_a_link_that_reads_as_its_address_prints_once(self):
		self.assertEqual(
			blocks(
				'<p><a href="https://example.com">https://example.com</a> <a href="mailto:info@example.com">info@example.com</a></p>'
			),
			["<p>https://example.com info@example.com</p>"],
		)

	def test_a_mail_link_prints_the_address_without_its_scheme(self):
		self.assertEqual(
			blocks('<p><a href="mailto:info@example.com">Schreiben Sie uns</a></p>'),
			["<p>Schreiben Sie uns (info@example.com)</p>"],
		)

	def test_a_link_of_another_kind_prints_its_text_only(self):
		self.assertEqual(
			blocks('<p><a href="javascript:alert(1)">hier</a> <a href="/app/x">da</a> <a>dort</a></p>'),
			["<p>hier da dort</p>"],
		)


class ListTest(TestCase):
	def test_a_list_of_the_editor_prints_with_bullets_and_numbers(self):
		content = (
			'<ol><li data-list="bullet"><span class="ql-ui" contenteditable="false"></span>Punkt</li>'
			'<li data-list="bullet">Noch einer</li></ol>'
			'<ol><li data-list="ordered">Erstens</li><li data-list="ordered">Zweitens</li></ol>'
		)
		self.assertEqual(
			blocks(content),
			[
				'<div class="bb-list">'
				'<div class="bb-li bb-level-0"><span class="bb-li-mark">•</span>Punkt</div>'
				'<div class="bb-li bb-level-0"><span class="bb-li-mark">•</span>Noch einer</div>'
				"</div>",
				'<div class="bb-list">'
				'<div class="bb-li bb-level-0"><span class="bb-li-mark">1.</span>Erstens</div>'
				'<div class="bb-li bb-level-0"><span class="bb-li-mark">2.</span>Zweitens</div>'
				"</div>",
			],
		)

	def test_an_indented_item_of_the_editor_is_a_level_deeper_and_numbers_anew(self):
		content = (
			'<ol><li data-list="ordered">A</li>'
			'<li data-list="ordered" class="ql-indent-1">a</li>'
			'<li data-list="ordered" class="ql-indent-1">b</li>'
			'<li data-list="ordered" class="ql-indent-2">i</li>'
			'<li data-list="ordered" class="ql-indent-2">ii</li>'
			'<li data-list="bullet" class="ql-indent-1">x</li>'
			'<li data-list="ordered">B</li>'
			'<li data-list="ordered" class="ql-indent-1">a</li></ol>'
		)
		marks = [part.split("</span>")[0] for part in html(content).split('class="bb-li-mark">')[1:]]
		self.assertEqual(marks, ["1.", "a)", "b)", "i.", "ii.", "\u2013", "2.", "a)"])
		self.assertIn(
			'<div class="bb-li bb-level-2"><span class="bb-li-mark">ii.</span>ii</div>', html(content)
		)

	def test_nested_lists_of_a_word_processor_are_levels_too(self):
		content = "<ul><li>A<ul><li>B<ul><li>C<ul><li>D</li></ul></li></ul></li></ul></li></ul><ol><li>Eins</li></ol>"
		self.assertEqual(
			blocks(content),
			[
				'<div class="bb-list">'
				'<div class="bb-li bb-level-0"><span class="bb-li-mark">•</span>A</div>'
				'<div class="bb-li bb-level-1"><span class="bb-li-mark">\u2013</span>B</div>'
				'<div class="bb-li bb-level-2"><span class="bb-li-mark">·</span>C</div>'
				'<div class="bb-li bb-level-3"><span class="bb-li-mark">•</span>D</div>'
				"</div>",
				'<div class="bb-list"><div class="bb-li bb-level-0"><span class="bb-li-mark">1.</span>Eins</div></div>',
			],
		)

	def test_deep_levels_stop_at_the_fourth(self):
		self.assertIn('bb-level-3"', html('<ol><li data-list="bullet" class="ql-indent-6">tief</li></ol>'))

	def test_numbers_run_on_past_the_alphabet_and_roman_numerals(self):
		items = "".join(f'<li data-list="ordered" class="ql-indent-{level}">x</li>' for level in (1,) * 28)
		marks = [
			part.split("</span>")[0] for part in html(f"<ol>{items}</ol>").split('class="bb-li-mark">')[1:]
		]
		self.assertEqual(marks[25:], ["z)", "aa)", "ab)"])
		self.assertEqual(body.roman(1994), "mcmxciv")

	def test_a_checklist_of_the_editor_prints_as_bullets(self):
		self.assertIn("•</span>offen", html('<ol><li data-list="unchecked">offen</li></ol>'))

	def test_an_empty_list_prints_nothing(self):
		self.assertEqual(blocks("<ul></ul><ol><li></li></ol><p>A</p>"), ["<p>A</p>"])

	def test_an_item_keeps_its_inline_markup(self):
		self.assertIn("<strong>wichtig</strong>", html("<ul><li><b>wichtig</b></li></ul>"))


class TableTest(TestCase):
	def test_a_table_of_the_editor_prints_as_a_table_of_the_letter(self):
		content = (
			'<table class="table table-bordered" style="width:900px"><tbody>'
			'<tr><td data-row="r1" style="background:red">Leistung</td><td data-row="r1">Termin</td></tr>'
			'<tr><td data-row="r2">Wartung</td><td data-row="r2">März</td></tr>'
			"</tbody></table>"
		)
		self.assertEqual(
			blocks(content),
			[
				'<table class="bb-text-table"><tbody>'
				"<tr><td>Leistung</td><td>Termin</td></tr>"
				"<tr><td>Wartung</td><td>März</td></tr>"
				"</tbody></table>"
			],
		)

	def test_the_head_of_a_table_is_kept_to_repeat_on_every_page(self):
		self.assertEqual(
			blocks("<table><thead><tr><th>A</th></tr></thead><tr><td>1</td></tr></table>"),
			[
				'<table class="bb-text-table"><thead><tr><th>A</th></tr></thead><tbody><tr><td>1</td></tr></tbody></table>'
			],
		)

	def test_a_cell_keeps_its_span_and_its_paragraphs_become_lines(self):
		self.assertEqual(
			blocks(
				'<table><tr><td colspan="2" rowspan="x"><p class="MsoNormal">A</p><p>B</p></td></tr></table>'
			),
			['<table class="bb-text-table"><tbody><tr><td colspan="2">A<br>B</td></tr></tbody></table>'],
		)

	def test_a_span_beyond_reason_is_dropped(self):
		self.assertNotIn("colspan", html('<table><tr><td colspan="99">A</td></tr></table>'))

	def test_a_table_without_rows_prints_nothing(self):
		self.assertEqual(blocks("<table><tbody></tbody></table><p>A</p>"), ["<p>A</p>"])

	def test_a_table_cell_holds_no_block_of_its_own(self):
		self.assertEqual(
			blocks("<table><tr><td><ul><li>A</li></ul><h2>B</h2></td></tr></table>"),
			['<table class="bb-text-table"><tbody><tr><td>A<br>B</td></tr></tbody></table>'],
		)


class ImageTest(TestCase):
	"""An image prints only as a data URL its file gives: a printout loads nothing (AGENTS.md)."""

	def test_an_image_of_the_files_of_the_site_prints_as_data(self):
		self.assertEqual(
			blocks('<p><img src="/files/logo.png" width="120" style="float:right"></p>', files),
			[f'<p><img class="bb-image" src="{PNG}" alt="" style="width: 120px;"></p>'],
		)

	def test_an_image_from_elsewhere_or_without_a_source_is_dropped(self):
		self.assertEqual(blocks('<p><img src="https://example.com/x.png">A<img></p>', files), ["<p>A</p>"])

	def test_a_resolver_may_only_give_an_image_as_data(self):
		for given in (
			"https://example.com/x.png",
			'data:image/png;base64,AA"onload="x',
			"data:text/html;base64,AA",
			"data:image/svg+xml;base64,AA",
		):
			with self.subTest(given=given):
				self.assertEqual(
					blocks('<p><img src="/files/x.png"></p>', lambda _source, given=given: given), []
				)

	def test_a_width_beyond_reason_is_dropped(self):
		self.assertEqual(
			blocks(
				'<p><img src="/files/logo.png" width="99999"></p><p><img src="/files/logo.png" width="abc"></p>',
				files,
			),
			[f'<p><img class="bb-image" src="{PNG}" alt=""></p>'] * 2,
		)

	def test_a_paragraph_with_an_image_alone_is_not_empty(self):
		found = body.render('<p><img src="/files/logo.png"></p>', files)
		self.assertFalse(found.empty)
		self.assertEqual([block.kind for block in found.blocks], ["paragraph"])

	def test_an_image_in_a_table_cell_prints_there(self):
		self.assertIn(
			f'<td><img class="bb-image" src="{PNG}" alt=""></td>',
			html('<table><tr><td><img src="/files/logo.png"></td></tr></table>', files),
		)


class EmptyTest(TestCase):
	def test_a_letter_without_text_is_empty(self):
		for content in (
			"",
			" ",
			None,
			"<p><br></p>",
			'<div class="ql-editor"><p> </p><p>\u00a0</p></div>',
			"<script>x</script>",
		):
			with self.subTest(content=content):
				self.assertTrue(body.render(content, no_images).empty)

	def test_a_letter_with_text_is_not_empty(self):
		self.assertFalse(body.render("<p>A</p>", no_images).empty)


class KeepTest(TestCase):
	"""The breaks of a long letter: a heading stays with what follows it, and the closing lines with the last
	paragraph, so that no page begins with a closing alone or ends with a heading."""

	def test_the_closing_lines_stay_with_the_last_paragraph(self):
		content = (
			"<p>Sehr geehrte Frau Muster,</p>"
			f"<p>{LONG}</p>"
			f"<p>{TWO_LINES}</p>"
			"<p>Mit freundlichen Grüßen</p><p><br></p><p><br></p><p>Erika Mustermann</p><p>Geschäftsführerin</p>"
		)
		self.assertEqual(
			html(content),
			"<p>Sehr geehrte Frau Muster,</p>\n"
			f"<p>{LONG.strip()}</p>\n"
			f'<div class="bb-keep"><p>{TWO_LINES}</p>\n'
			"<p>Mit freundlichen Grüßen</p>\n"
			'<p class="bb-blank"></p>\n<p class="bb-blank"></p>\n'
			"<p>Erika Mustermann</p>\n<p>Geschäftsführerin</p></div>",
		)

	def test_a_heading_stays_with_what_follows(self):
		content = f"<p>{LONG}</p><h2>Ablauf</h2><p><br></p><ul><li>A</li></ul><p>{LONG}</p><p>{LONG}</p>"
		self.assertIn(
			'<div class="bb-keep"><div class="bb-heading">Ablauf</div>\n<p class="bb-blank"></p>\n<div class="bb-list">',
			html(content),
		)

	def test_a_heading_right_before_the_closing_joins_it(self):
		content = f"<p>{LONG}</p><h2>Ablauf</h2><p><br></p><p>{LONG}</p>"
		self.assertIn('<div class="bb-keep"><div class="bb-heading">Ablauf</div>', html(content))
		self.assertEqual(html(content).count("bb-keep"), 1)

	def test_a_bold_line_alone_counts_as_a_heading(self):
		content = "<p><strong>Ablauf</strong></p><p>Ein Absatz danach, der lang genug ist, um keine Schlusszeile zu sein und ein wenig mehr.</p><p>Und noch ein letzter Absatz, der lang genug ist, um keine Schlusszeile zu sein.</p>"
		found = body.blocks(content, no_images)
		self.assertEqual([block.kind for block in found], ["heading", "paragraph", "paragraph"])
		self.assertTrue(
			html(content).startswith('<div class="bb-keep"><p><strong>Ablauf</strong></p>\n<p>Ein Absatz')
		)

	def test_a_long_bold_paragraph_is_no_heading(self):
		text = "Wichtig " * 20
		self.assertEqual(body.blocks(f"<p><b>{text}</b></p>", no_images)[0].kind, "paragraph")

	def test_a_heading_at_the_end_stays_with_the_closing(self):
		self.assertEqual(
			html("<p>A</p><h2>Ende</h2>"),
			'<div class="bb-keep"><p>A</p>\n<div class="bb-heading">Ende</div></div>',
		)

	def test_a_heading_before_the_closing_joins_its_group(self):
		content = f"<p>{LONG}</p><h2>Kurz</h2><p>{TWO_LINES}</p><p>Gruß</p>"
		self.assertEqual(html(content).count('class="bb-keep"'), 1)
		self.assertIn('<div class="bb-keep"><div class="bb-heading">Kurz</div>', html(content))

	def test_a_long_run_of_short_lines_keeps_only_its_end_together(self):
		content = "".join(f"<p>Zeile {number}</p>" for number in range(30))
		found = html(content)
		self.assertIn('<div class="bb-keep"><p>Zeile 21</p>', found)
		self.assertTrue(found.startswith("<p>Zeile 0</p>"))

	def test_a_letter_that_ends_in_a_table_or_list_keeps_nothing_extra(self):
		self.assertNotIn("bb-keep", html("<p>A</p><ul><li>B</li></ul>"))
		self.assertNotIn("bb-keep", html("<p>A</p><table><tr><td>B</td></tr></table>"))

	def test_the_closing_after_a_list_keeps_with_the_list(self):
		found = html(f"<p>{LONG}{LONG}</p><ul><li>B</li></ul><p>Gruß</p>")
		self.assertIn('<div class="bb-keep"><div class="bb-list">', found)

	def test_the_closing_after_a_table_starts_its_own_group(self):
		found = html("<table><tr><td>B</td></tr></table><p>Gruß</p><p>Name</p>")
		self.assertTrue(found.endswith('<div class="bb-keep"><p>Gruß</p>\n<p>Name</p></div>'))

	def test_an_empty_letter_has_no_blocks(self):
		self.assertEqual(html(""), "")

	def test_blank_lines_at_the_start_and_end_print_nothing(self):
		self.assertEqual(blocks("<p><br></p><p>A</p><p><br></p>"), ["<p>A</p>"])


class ParserTest(TestCase):
	def test_an_end_tag_without_its_start_is_ignored(self):
		self.assertEqual(blocks("<p>A</strong></td>B</p>"), ["<p>AB</p>"])

	def test_an_unclosed_tag_ends_with_the_content(self):
		self.assertEqual(blocks("<p><b>A"), ["<p><strong>A</strong></p>"])

	def test_a_declaration_or_processing_instruction_prints_nothing(self):
		self.assertEqual(
			blocks("<!DOCTYPE html><?xml version='1.0'?><![if !supportLists]>A<![endif]>"), ["<p>A</p>"]
		)

	def test_an_unknown_tag_keeps_its_text(self):
		self.assertEqual(blocks("<p><o:p>A</o:p><custom-tag>B</custom-tag></p>"), ["<p>AB</p>"])

	def test_what_a_dropped_element_holds_is_dropped_however_it_is_nested(self):
		self.assertEqual(
			blocks("<object><p>x</p><br><b>y</object><canvas></p>z</canvas><p>A</p>"), ["<p>A</p>"]
		)

	def test_a_division_without_blocks_is_a_paragraph(self):
		self.assertEqual(blocks("<div>A</div><div>B</div>"), ["<p>A</p>", "<p>B</p>"])

	def test_an_empty_heading_prints_nothing(self):
		self.assertEqual(blocks("<h2> </h2><p>A</p>"), ["<p>A</p>"])

	def test_only_the_items_of_a_list_print(self):
		self.assertEqual(
			blocks("<ul> Text <p>x</p><li>A</li></ul>"),
			[
				'<div class="bb-list"><div class="bb-li bb-level-0"><span class="bb-li-mark">•</span>A</div></div>'
			],
		)

	def test_only_the_rows_of_a_table_print(self):
		self.assertEqual(
			blocks("<table> <caption>C</caption><tr></tr><tfoot><tr><td>A</td></tr></tfoot></table>"),
			['<table class="bb-text-table"><tbody><tr><td>A</td></tr></tbody></table>'],
		)


class ClosingHeadingTest(TestCase):
	def test_a_heading_with_a_blank_line_before_the_closing_joins_it(self):
		eight_lines = LONG + "x" * 100
		found = html(f"<p>{LONG}</p><h2>Ablauf</h2><p><br></p><p>{eight_lines}</p>")
		self.assertIn(
			'<div class="bb-keep"><div class="bb-heading">Ablauf</div>\n<p class="bb-blank"></p>\n<p>', found
		)
		self.assertEqual(found.count("bb-keep"), 1)
