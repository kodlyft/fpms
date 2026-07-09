// Copyright (c) 2026, Kodlyft and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Order", {
	refresh(frm) {
		const open = !["Closed", "Completed", "Delivered"].includes(frm.doc.status);
		if (frm.doc.docstatus === 1 && open && flt(frm.doc.per_received) < 100) {
			frm.add_custom_button(
				__("Tanker Receipt"),
				() => {
					frappe.model.open_mapped_doc({
						method: "fpms.fuel_pump_management_system.doctype.tanker_receipt.tanker_receipt.make_tanker_receipt",
						frm: frm,
					});
				},
				__("Create"),
			);
		}
	},
});
