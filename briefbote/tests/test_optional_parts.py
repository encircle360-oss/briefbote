"""The parts Briefbote adds for the Business Letter of erpnext_germany, on a site with and on one without the app:
the print format Geschäftsbrief and the entries of sidebar and workspace exist exactly where the DocType does. CI
runs this module on the site before it installs erpnext_germany and again after."""

import unittest
from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path
from frappe.tests import IntegrationTestCase

from briefbote.briefbote import optional
from briefbote.tests import optional_parts as parts

APP = Path(frappe.get_app_path("briefbote"))
SIDEBAR_FILE = APP / "briefbote" / "sidebar" / "briefbote" / "briefbote.json"
WORKSPACE_FILE = APP / "briefbote" / "workspace" / "geschäftspost" / "geschäftspost.json"


def with_app() -> bool:
	return bool(frappe.db.exists("DocType", "Business Letter"))


class OptionalPartsTest(IntegrationTestCase):
	def test_the_parts_exist_exactly_where_the_doctype_does(self):
		self.assertEqual(parts.problems(with_app()), [])

	def test_a_second_sync_changes_nothing(self):
		before = parts.state()
		optional.sync()
		optional.sync()
		self.assertEqual(parts.state(), before)

	def test_the_files_imported_anew_get_the_parts_again_where_the_doctype_exists(self):
		"""bench migrate imports the sidebar and the workspace from their files when they change, which drops the
		rows Briefbote added; the sync after the migration puts them back, or leaves them out without the app."""
		import_file_by_path(str(SIDEBAR_FILE), force=True)
		import_file_by_path(str(WORKSPACE_FILE), force=True)
		optional.sync()
		self.assertEqual(parts.problems(with_app()), [])

	def test_the_print_format_is_never_written_to_the_files_of_the_app(self):
		"""In developer mode Frappe exports a standard print format it saves; this one is imported, not saved."""
		self.assertFalse(
			(APP / "briefbote" / "print_format" / "geschäftsbrief" / "geschäftsbrief.json").exists()
		)


class OptionalPartsWithAppTest(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not with_app():
			raise unittest.SkipTest(
				"erpnext_germany is not installed; CI runs this module again after installing it"
			)

	def tearDown(self):
		optional.sync()

	def test_the_parts_go_with_the_doctype_and_come_back_with_it(self):
		optional.sync(exists=lambda _doctype: False)
		found = parts.state()
		self.assertEqual(
			(found.print_formats, found.sidebar, found.shortcuts, found.blocks), ((), (), (), ())
		)
		optional.sync()
		self.assertEqual(parts.problems(True), [])

	def test_the_app_being_uninstalled_takes_its_parts_away_before_its_doctypes_go(self):
		optional.app_uninstalling("erpnext_germany")
		found = parts.state()
		self.assertEqual(
			(found.print_formats, found.sidebar, found.shortcuts, found.blocks), ((), (), (), ())
		)

	def test_another_app_being_uninstalled_leaves_the_parts(self):
		optional.app_uninstalling("eu_einvoice")
		self.assertEqual(parts.problems(True), [])

	def test_an_app_installed_later_brings_the_parts(self):
		optional.sync(exists=lambda _doctype: False)
		optional.app_installed("erpnext_germany")
		self.assertEqual(parts.problems(True), [])

	def test_the_print_format_prints_from_the_file_of_the_app(self):
		record = frappe.get_doc("Print Format", "Geschäftsbrief")
		self.assertEqual(
			(record.doc_type, record.module, record.standard), ("Business Letter", "Briefbote", "Yes")
		)
		self.assertFalse(record.html)
		self.assertTrue(
			(APP / "briefbote" / "print_format" / "geschäftsbrief" / "geschäftsbrief.html").exists()
		)
