// Copyright (c) 2026, Kodlyft and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tanker Receipt", {
	setup: function (frm) {
		frm.set_query("tank", "items", function () {
			return {
				filters: {
					status: "Active",
					company: frm.doc.company,
				},
			};
		});

		frm.set_query("component", "charges", function () {
			return {
				filters: {
					disabled: 0,
					company: frm.doc.company,
				},
			};
		});

		frm.set_query("account", "charges", function () {
			return {
				filters: {
					company: frm.doc.company,
					disabled: 0,
					is_group: 0,
					account_type: [
						"IN",
						["Tax", "Chargeable", "Expense Account", "Expenses Included In Valuation"],
					],
				},
			};
		});
	},

	refresh: function (frm) {
		if (frm.doc.docstatus === 1 && frm.doc.purchase_receipt && !frm.doc.purchase_invoice) {
			frm.add_custom_button(
				__("Purchase Invoice"),
				() => {
					frappe.model.open_mapped_doc({
						method: "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
						source_name: frm.doc.purchase_receipt,
						frm: frm,
					});
				},
				__("Create"),
			);
		}
	},
});
