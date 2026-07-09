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
			"label": _("Dip Reading"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Dip Reading",
			"width": 160,
		},
		{"label": _("Date/Time"), "fieldname": "reading_datetime", "fieldtype": "Datetime", "width": 160},
		{"label": _("Tank"), "fieldname": "tank", "fieldtype": "Link", "options": "Tank", "width": 120},
		{"label": _("Fuel Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": _("Dip Volume (L)"), "fieldname": "volume_litres", "fieldtype": "Float", "width": 130},
		{"label": _("Book Stock (L)"), "fieldname": "book_stock", "fieldtype": "Float", "width": 130},
		{"label": _("Variance (L)"), "fieldname": "variance_litres", "fieldtype": "Float", "width": 120},
		{"label": _("Variance %"), "fieldname": "variance_pct", "fieldtype": "Percent", "width": 100},
		{"label": _("Within Tolerance"), "fieldname": "within_tolerance", "fieldtype": "Check", "width": 120},
	]


def get_data(filters):
	conditions = {"docstatus": 1}
	if filters.get("tank"):
		conditions["tank"] = filters["tank"]
	if filters.get("from_date") and filters.get("to_date"):
		conditions["reading_datetime"] = ["between", [filters["from_date"], filters["to_date"]]]

	return frappe.get_all(
		"Dip Reading",
		filters=conditions,
		fields=[
			"name",
			"reading_datetime",
			"tank",
			"item",
			"volume_litres",
			"book_stock",
			"variance_litres",
			"variance_pct",
			"within_tolerance",
		],
		order_by="reading_datetime desc",
	)
