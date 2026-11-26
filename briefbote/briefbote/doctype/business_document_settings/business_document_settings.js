// The check of the settings (briefbote.briefbote.setup.check) from the form: what the company lacks for its
// printouts, each finding marked by its level.
frappe.ui.form.on("Business Document Settings", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		frm.add_custom_button(__("Check Settings"), () => {
			frappe
				.call({ method: "briefbote.briefbote.setup.check", args: { company: frm.doc.company } })
				.then(({ message }) => {
					const colours = { error: "red", warning: "orange", info: "blue" };
					const rows = (message || []).map(
						({ level, message: text }) =>
							`<p><span class="indicator-pill ${colours[level] || "gray"}"></span> ${frappe.utils.escape_html(text)}</p>`
					);
					frappe.msgprint({
						title: __("Settings Check"),
						message: rows.length ? rows.join("") : __("Nothing is missing."),
						indicator: rows.length ? "orange" : "green",
					});
				});
		});
	},
});
