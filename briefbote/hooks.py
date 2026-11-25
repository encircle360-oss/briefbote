app_name = "briefbote"
app_title = "Briefbote"
app_publisher = "encircle360 GmbH"
app_description = "Print formats for the business documents of German companies in ERPNext, laid out to DIN 5008: from the quotation through invoice, credit note and dunning letter to the purchase order"
app_email = "oss@encircle360.com"
app_license = "AGPL-3.0-or-later"
app_home = "/desk/geschäftspost"

required_apps = ["frappe/erpnext"]

# The apps screen and the app switcher of the desk list an app from this entry. Briefbote also mounts its dock on the
# rail of ERPNext (dock/briefbote), and where the desk has that rail, Frappe keeps a mounted app off the apps screen;
# the entry still offers Briefbote as the default app of a user.
add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/briefbote/images/briefbote-logo.svg",
		"title": app_title,
		"route": app_home,
		"has_permission": "briefbote.permissions.has_app_permission",
	}
]

# The icon of the module on the rail and in the header of its sidebar.
app_include_icons = ["/assets/briefbote/icons/module-icons.svg"]

# The block Über Briefbote of the workspace is a Custom HTML Block, which has no module; bench migrate imports it
# anew each time.
fixtures = [
	{"dt": "Custom HTML Block", "filters": [["name", "=", "Über Briefbote"]]},
]

# What the print formats read beyond the fields of their document (briefbote/briefbote/printing.py).
jinja = {
	"methods": [
		"briefbote.briefbote.printing.briefbote_letter",
		"briefbote.briefbote.printing.briefbote_invoice",
	]
}
