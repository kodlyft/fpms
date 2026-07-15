# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe


def link_tanker_receipt(doc, method: str | None = None) -> None:
	"""``on_submit`` hook on Purchase Invoice."""
	_set_purchase_invoice(doc, doc.name)


def unlink_tanker_receipt(doc, method: str | None = None) -> None:
	"""``on_cancel`` hook on Purchase Invoice."""
	_set_purchase_invoice(doc, None)


def _set_purchase_invoice(invoice, value: str | None) -> None:
	receipts = {row.purchase_receipt for row in invoice.items if row.get("purchase_receipt")}
	if not receipts:
		return

	filters = {"purchase_receipt": ["in", sorted(receipts)], "docstatus": 1}
	if value is None:
		filters["purchase_invoice"] = invoice.name

	for name in frappe.get_all("Tanker Receipt", filters=filters, pluck="name"):
		frappe.db.set_value("Tanker Receipt", name, "purchase_invoice", value)
