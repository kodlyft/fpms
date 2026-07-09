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
			"label": _("Shift"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Shift Reconciliation",
			"width": 160,
		},
		{"label": _("Date"), "fieldname": "shift_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Shift Type"),
			"fieldname": "shift_type",
			"fieldtype": "Link",
			"options": "Shift Type",
			"width": 110,
		},
		{
			"label": _("Attendant"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{"label": _("Fuel (L)"), "fieldname": "total_fuel_litres", "fieldtype": "Float", "width": 110},
		{"label": _("Fuel Sales"), "fieldname": "total_fuel_sales", "fieldtype": "Currency", "width": 130},
		{"label": _("Collected"), "fieldname": "total_collected", "fieldtype": "Currency", "width": 130},
		{"label": _("Variance"), "fieldname": "variance_amount", "fieldtype": "Currency", "width": 120},
		{"label": _("Status"), "fieldname": "variance_status", "fieldtype": "Data", "width": 100},
	]


def get_data(filters):
	conditions = {"docstatus": 1}
	if filters.get("shift_type"):
		conditions["shift_type"] = filters["shift_type"]
	if filters.get("employee"):
		conditions["employee"] = filters["employee"]
	if filters.get("from_date") and filters.get("to_date"):
		conditions["shift_date"] = ["between", [filters["from_date"], filters["to_date"]]]

	return frappe.get_all(
		"Shift Reconciliation",
		filters=conditions,
		fields=[
			"name",
			"shift_date",
			"shift_type",
			"employee",
			"total_fuel_litres",
			"total_fuel_sales",
			"total_collected",
			"variance_amount",
			"variance_status",
		],
		order_by="shift_date desc",
	)
