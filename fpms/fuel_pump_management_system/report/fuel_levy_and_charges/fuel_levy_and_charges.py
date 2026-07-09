# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Tanker Receipt"),
			"fieldname": "tanker",
			"fieldtype": "Link",
			"options": "Tanker Receipt",
			"width": 150,
		},
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 150,
		},
		{"label": _("Fuel Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 130},
		{"label": _("Component"), "fieldname": "component", "fieldtype": "Data", "width": 200},
		{"label": _("Received (L)"), "fieldname": "received_litres", "fieldtype": "Float", "width": 110},
		{"label": _("Rate / Litre"), "fieldname": "rate_per_litre", "fieldtype": "Currency", "width": 100},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 130},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 150,
		},
	]


def get_data(filters):
	charge_filters = {"parenttype": "Tanker Receipt"}
	if filters.get("component"):
		charge_filters["component"] = filters["component"]

	charges = frappe.get_all(
		"Fuel Purchase Charge",
		filters=charge_filters,
		fields=["parent as tanker", "component", "rate_per_litre", "amount", "account"],
		order_by="creation desc",
	)
	if not charges:
		return []

	tankers = {c["tanker"] for c in charges}
	parents = {
		t.name: t
		for t in frappe.get_all(
			"Tanker Receipt",
			filters={"name": ["in", list(tankers)], "docstatus": 1},
			fields=["name", "posting_date", "supplier", "item", "received_litres"],
		)
	}

	from_date, to_date = filters.get("from_date"), filters.get("to_date")
	supplier = filters.get("supplier")

	data = []
	for c in charges:
		parent = parents.get(c["tanker"])
		if not parent:  # skip drafts / cancelled
			continue
		if supplier and parent.supplier != supplier:
			continue
		if from_date and to_date and not (from_date <= str(parent.posting_date) <= to_date):
			continue
		data.append(
			{
				**c,
				"posting_date": parent.posting_date,
				"supplier": parent.supplier,
				"item": parent.item,
				"received_litres": parent.received_litres,
			}
		)
	return data
