"""Who the desk offers Briefbote to."""

import frappe

# The roles of the workspace Geschäftspost; the settings grant theirs to the same roles.
APP_ROLES = frozenset({"Accounts Manager", "Accounts User", "System Manager"})


def has_app_permission() -> bool:
	"""Whether the apps screen of the desk lists Briefbote for the session user."""
	return not APP_ROLES.isdisjoint(frappe.get_roles())
