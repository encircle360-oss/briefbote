"""The block Über Briefbote for the desk, in the language of the user (the pure part is about.py)."""

import frappe
from frappe import _

from briefbote.briefbote import about


@frappe.whitelist()
def render() -> str:
	return about.render(_)
