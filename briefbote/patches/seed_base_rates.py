"""Give the Einstellungen Geschäftspost that were made before the base rates the rates the Bundesbank has published."""

import frappe

from briefbote.briefbote.doctype.business_document_settings.business_document_settings import seed_base_rates


def execute():
	for name in frappe.get_all("Business Document Settings", pluck="name"):
		settings = frappe.get_doc("Business Document Settings", name)
		if not settings.get("base_rates"):
			seed_base_rates(settings)
			settings.save(ignore_permissions=True)
