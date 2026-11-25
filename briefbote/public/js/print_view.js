// The print view of the desk (frappe/printing/page/print/print.js) prints a format through the browser: its button
// Drucken, and Ctrl+P on it, open the page /printview and call window.print() on it. The running foot with the page
// numbers and the breaks of Briefbote's formats come from the PDF generator, which the button PDF uses. For a print
// format of the module Briefbote, Drucken therefore prints the PDF of the generator: it fetches the PDF the button PDF
// would download, loads it into a hidden frame and opens the print dialog of the browser on it. Every other format,
// a print server and raw printing keep the way of Frappe.
(() => {
	const PrintView = frappe.ui.form.PrintView;
	if (!PrintView || PrintView.prototype.briefbote_printit) {
		return;
	}
	const MODULE = "Briefbote";
	const TIMEOUT_MS = 120000;
	PrintView.prototype.briefbote_printit = PrintView.prototype.printit;

	PrintView.prototype.prints_briefbote_pdf = function () {
		const format = this.get_print_format();
		return (
			format.module === MODULE &&
			!format.raw_printing &&
			!cint(this.print_settings.enable_print_server) &&
			!this.get_mapped_printer().length
		);
	};

	PrintView.prototype.briefbote_pdf_url = function () {
		const format = this.get_print_format();
		return this.get_page_url(
			"/api/method/frappe.utils.print_format.download_pdf?",
			false,
			format.pdf_generator
		);
	};

	PrintView.prototype.printit = function () {
		if (!this.prints_briefbote_pdf()) {
			return this.briefbote_printit();
		}
		let frame;
		let url;
		let timer;
		const cleanup = () => {
			clearTimeout(timer);
			frame?.remove();
			if (url) {
				URL.revokeObjectURL(url);
			}
		};
		const fail = () => {
			frappe.dom.unfreeze();
			cleanup();
			frappe.msgprint(__("The PDF could not be printed. Download it with PDF and print it from there."));
		};
		frappe.dom.freeze(__("Preparing the PDF for printing …"));
		fetch(this.briefbote_pdf_url(), { credentials: "same-origin" })
			.then((response) => {
				if (!response.ok) {
					throw new Error(response.statusText);
				}
				return response.blob();
			})
			.then((blob) => {
				url = URL.createObjectURL(new Blob([blob], { type: "application/pdf" }));
				frame = document.createElement("iframe");
				frame.className = "briefbote-print-frame";
				frame.style.cssText = "position: fixed; right: 0; bottom: 0; width: 0; height: 0; border: 0;";
				timer = setTimeout(fail, TIMEOUT_MS);
				frame.onload = () => {
					clearTimeout(timer);
					frappe.dom.unfreeze();
					try {
						frame.contentWindow.focus();
						frame.contentWindow.print();
					} catch (error) {
						fail();
						return;
					}
					// The print dialog keeps the frame until it closes; it goes when the user is done.
					timer = setTimeout(cleanup, 600000);
				};
				frame.src = url;
				document.body.appendChild(frame);
			})
			.catch(fail);
	};
})();
