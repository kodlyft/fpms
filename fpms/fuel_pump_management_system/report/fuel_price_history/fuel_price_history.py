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
			"label": _("Notification"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Fuel Price Notification",
			"width": 160,
		},
		{"label": _("Effective From"), "fieldname": "effective_from", "fieldtype": "Datetime", "width": 160},
		{"label": _("Fuel Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": _("Ex-Depot"), "fieldname": "ex_depot_price", "fieldtype": "Currency", "width": 110},
		{"label": _("Dealer Comm."), "fieldname": "dealer_commission", "fieldtype": "Currency", "width": 110},
		{"label": _("OMC Margin"), "fieldname": "omc_margin", "fieldtype": "Currency", "width": 110},
		{"label": _("PDL"), "fieldname": "pdl_per_litre", "fieldtype": "Currency", "width": 100},
		{"label": _("Climate Levy"), "fieldname": "climate_levy", "fieldtype": "Currency", "width": 110},
		{"label": _("Retail Price"), "fieldname": "retail_price", "fieldtype": "Currency", "width": 120},
		{"label": _("OGRA Ref"), "fieldname": "ogra_reference", "fieldtype": "Data", "width": 130},
	]


def get_data(filters):
	conditions = {"docstatus": 1}
	if filters.get("item"):
		conditions["item"] = filters["item"]
	if filters.get("from_date") and filters.get("to_date"):
		conditions["effective_from"] = ["between", [filters["from_date"], filters["to_date"]]]

	return frappe.get_all(
		"Fuel Price Notification",
		filters=conditions,
		fields=[
			"name",
			"effective_from",
			"item",
			"ex_depot_price",
			"dealer_commission",
			"omc_margin",
			"pdl_per_litre",
			"climate_levy",
			"retail_price",
			"ogra_reference",
		],
		order_by="effective_from desc",
	)
