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
			"fieldname": "shift",
			"fieldtype": "Link",
			"options": "Shift Reconciliation",
			"width": 150,
		},
		{"label": _("Date"), "fieldname": "shift_date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 170,
		},
		{
			"label": _("Fuel Card"),
			"fieldname": "fuel_card",
			"fieldtype": "Link",
			"options": "Fuel Card",
			"width": 110,
		},
		{"label": _("Vehicle"), "fieldname": "vehicle_number", "fieldtype": "Data", "width": 100},
		{"label": _("Fuel Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 130},
		{"label": _("Litres"), "fieldname": "litres", "fieldtype": "Float", "width": 90},
		{"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 90},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = {"parenttype": "Shift Reconciliation", "docstatus": 1}
	if filters.get("customer"):
		conditions["customer"] = filters["customer"]

	rows = frappe.get_all(
		"Fuel Credit Sale",
		filters=conditions,
		fields=[
			"parent as shift",
			"customer",
			"fuel_card",
			"vehicle_number",
			"item",
			"litres",
			"rate",
			"amount",
			"sales_invoice",
		],
		order_by="creation desc",
	)

	shift_dates = {}
	if rows:
		names = list({r.shift for r in rows})
		for name, sdate in frappe.get_all(
			"Shift Reconciliation",
			filters={"name": ["in", names]},
			fields=["name", "shift_date"],
			as_list=True,
		):
			shift_dates[name] = sdate

	from_date, to_date = filters.get("from_date"), filters.get("to_date")
	data = []
	for r in rows:
		r["shift_date"] = shift_dates.get(r["shift"])
		if from_date and to_date and r["shift_date"] and not (from_date <= str(r["shift_date"]) <= to_date):
			continue
		data.append(r)
	return data
