// Copyright (c) 2026, Kodlyft and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fuel Charge Type", {
	setup: function (frm) {
		frm.set_query("default_account", function () {
			return {
				filters: {
					disabled: 0,
				},
			};
		});

		frm.set_query("default_account", function () {
			return {
				filters: {
					company: frm.doc.company,
					disabled: 0,
					is_group: 0,
					account_type: ["IN", ["Tax", "Chargeable"]],
				},
			};
		});
	},

	company: function (frm) {
		if (!frm.doc.company) {
			frm.doc.default_account = null;
			frm.refresh_field("default_account");
		}
	},
});
