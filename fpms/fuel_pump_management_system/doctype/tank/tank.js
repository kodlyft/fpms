// Copyright (c) 2026, Kodlyft and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tank", {
	setup: function (frm) {
		frm.set_query("warehouse", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
				},
			};
		});
	},

	company: function (frm) {
		if (!frm.doc.company) {
			frm.set_value("warehouse", "");
		}
	},
});
