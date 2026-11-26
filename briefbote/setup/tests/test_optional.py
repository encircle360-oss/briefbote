from unittest import TestCase

from briefbote.setup import optional

GROUP = {"type": "Section Break", "label": "Correspondence", "icon": "mail-pen", "indent": 1}
LETTERS = {
	"type": "Link",
	"child": 1,
	"label": "Business Letters",
	"link_type": "DocType",
	"link_to": "Business Letter",
}
TEMPLATES = {
	"type": "Link",
	"child": 1,
	"label": "Letter Templates",
	"link_type": "DocType",
	"link_to": "Business Letter Template",
}
OPTIONAL = [GROUP, LETTERS, TEMPLATES]
BASE = [
	{"type": "Link", "label": "Geschäftspost", "link_type": "Workspace", "link_to": "Geschäftspost"},
	{"type": "Section Break", "label": "Sales Documents", "link_type": "DocType"},
	{"type": "Link", "child": 1, "label": "Quotations", "link_type": "DocType", "link_to": "Quotation"},
]


def everything(_doctype: str) -> bool:
	return True


def nothing(_doctype: str) -> bool:
	return False


def apply(items, changes):
	add, remove = changes
	kept = [
		row for row in items if optional.identity(row) not in {optional.identity(gone) for gone in remove}
	]
	return kept + add


class SidebarTest(TestCase):
	def test_the_rows_of_a_doctype_that_exists_are_added_at_the_end(self):
		add, remove = optional.sidebar_changes(BASE, OPTIONAL, everything)
		self.assertEqual((add, remove), (OPTIONAL, []))

	def test_nothing_is_added_where_the_doctype_does_not_exist(self):
		self.assertEqual(optional.sidebar_changes(BASE, OPTIONAL, nothing), ([], []))

	def test_a_group_stands_only_with_an_entry(self):
		add, _remove = optional.sidebar_changes(BASE, OPTIONAL, lambda doctype: doctype == "Business Letter")
		self.assertEqual(add, [GROUP, LETTERS])

	def test_adding_twice_changes_nothing(self):
		once = apply(BASE, optional.sidebar_changes(BASE, OPTIONAL, everything))
		self.assertEqual(optional.sidebar_changes(once, OPTIONAL, everything), ([], []))

	def test_the_rows_go_when_the_doctype_goes(self):
		once = apply(BASE, optional.sidebar_changes(BASE, OPTIONAL, everything))
		add, remove = optional.sidebar_changes(once, OPTIONAL, nothing)
		self.assertEqual((add, remove), ([], OPTIONAL))
		self.assertEqual(apply(once, (add, remove)), BASE)

	def test_a_group_as_the_site_stores_it_is_the_same_group(self):
		"""A Sidebar Item has a default for link_type, so a stored group claims to link a DocType."""
		stored = [*BASE, {**GROUP, "link_type": "DocType", "link_to": None}, LETTERS, TEMPLATES]
		self.assertEqual(optional.sidebar_changes(stored, OPTIONAL, everything), ([], []))

	def test_a_missing_entry_is_added_to_a_group_that_is_there(self):
		self.assertEqual(
			optional.sidebar_changes([*BASE, GROUP, LETTERS], OPTIONAL, everything), ([TEMPLATES], [])
		)

	def test_rows_of_the_app_are_never_removed(self):
		_add, remove = optional.sidebar_changes(BASE, OPTIONAL, nothing)
		self.assertEqual(remove, [])


SHORTCUTS = [
	{"type": "DocType", "label": "Business Letters", "link_to": "Business Letter", "doc_view": "List"},
	{
		"type": "DocType",
		"label": "Letter Templates",
		"link_to": "Business Letter Template",
		"doc_view": "List",
	},
]
BLOCKS = [
	{"id": "bbhead002", "type": "header", "data": {"text": "Documents", "col": 12}},
	{"id": "bbshort13", "type": "shortcut", "data": {"shortcut_name": "Purchase Invoices", "col": 4}},
	{"id": "bbshort03", "type": "shortcut", "data": {"shortcut_name": "Print Formats", "col": 4}},
]


class WorkspaceTest(TestCase):
	def test_the_shortcuts_of_a_doctype_that_exists_are_added(self):
		current = [{"type": "DocType", "label": "Quotations", "link_to": "Quotation"}]
		self.assertEqual(optional.shortcut_changes(current, SHORTCUTS, everything), (SHORTCUTS, []))
		self.assertEqual(optional.shortcut_changes(current, SHORTCUTS, nothing), ([], []))

	def test_shortcuts_go_with_their_doctype_and_are_added_once(self):
		self.assertEqual(optional.shortcut_changes(SHORTCUTS, SHORTCUTS, everything), ([], []))
		self.assertEqual(optional.shortcut_changes(SHORTCUTS, SHORTCUTS, nothing), ([], SHORTCUTS))

	def test_the_blocks_follow_the_block_they_are_placed_after(self):
		found = optional.content(BLOCKS, SHORTCUTS, everything, "bbshort13")
		self.assertEqual(
			[block["id"] for block in found],
			["bbhead002", "bbshort13", "bbopt-business-letters", "bbopt-letter-templates", "bbshort03"],
		)
		self.assertEqual(
			found[2],
			{
				"id": "bbopt-business-letters",
				"type": "shortcut",
				"data": {"shortcut_name": "Business Letters", "col": 4},
			},
		)

	def test_placing_twice_changes_nothing(self):
		once = optional.content(BLOCKS, SHORTCUTS, everything, "bbshort13")
		self.assertEqual(optional.content(once, SHORTCUTS, everything, "bbshort13"), once)

	def test_a_missing_block_takes_its_place_among_the_others(self):
		partial = optional.content(BLOCKS, SHORTCUTS[1:], everything, "bbshort13")
		found = optional.content(partial, SHORTCUTS, everything, "bbshort13")
		self.assertEqual(found, optional.content(BLOCKS, SHORTCUTS, everything, "bbshort13"))

	def test_the_blocks_go_with_their_doctype(self):
		once = optional.content(BLOCKS, SHORTCUTS, everything, "bbshort13")
		self.assertEqual(optional.content(once, SHORTCUTS, nothing, "bbshort13"), BLOCKS)

	def test_without_the_block_to_follow_they_stand_at_the_end(self):
		found = optional.content(BLOCKS[:1], SHORTCUTS, everything, "bbshort13")
		self.assertEqual(
			[block["id"] for block in found],
			["bbhead002", "bbopt-business-letters", "bbopt-letter-templates"],
		)

	def test_a_block_a_person_moved_stays_where_it_is(self):
		moved = [
			BLOCKS[0],
			{
				"id": "bbopt-business-letters",
				"type": "shortcut",
				"data": {"shortcut_name": "Business Letters", "col": 4},
			},
			*BLOCKS[1:],
		]
		found = optional.content(moved, SHORTCUTS[:1], everything, "bbshort13")
		self.assertEqual(found, moved)


class PrintFormatTest(TestCase):
	def test_a_print_format_exists_where_its_doctype_does(self):
		self.assertTrue(optional.wanted({"doc_type": "Business Letter"}, everything))
		self.assertFalse(optional.wanted({"doc_type": "Business Letter"}, nothing))
