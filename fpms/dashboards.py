# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

"""
Connections between ERPNext documents and the FPMS documents that drive them.
"""

import frappe
from frappe import _


def purchase_order(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Tanker Receipt"],
		non_standard_fieldnames={"Tanker Receipt": "purchase_order"},
	)


def purchase_receipt(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Tanker Receipt"],
		non_standard_fieldnames={"Tanker Receipt": "purchase_receipt"},
	)


def purchase_invoice(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Tanker Receipt"],
		non_standard_fieldnames={"Tanker Receipt": "purchase_invoice"},
	)


def sales_invoice(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Shift Reconciliation"],
		internal_links={"Shift Reconciliation": "fpms_shift"},
	)


def item(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Tank", "Nozzle", "Fuel Price Notification", "Dip Reading", "Tanker Receipt"],
		non_standard_fieldnames={
			"Tank": "item",
			"Nozzle": "item",
			"Fuel Price Notification": "item",
			"Dip Reading": "item",
			"Tanker Receipt": "item",
		},
	)


def item_price(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Fuel Price Notification"],
		non_standard_fieldnames={"Fuel Price Notification": "item_price"},
	)


def warehouse(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Tank"],
		non_standard_fieldnames={"Tank": "warehouse"},
	)


def supplier(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Tanker Receipt"],
		non_standard_fieldnames={"Tanker Receipt": "supplier"},
	)


def customer(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Fleet", "Fuel Card"],
		non_standard_fieldnames={"Fleet": "customer", "Fuel Card": "customer"},
	)


def employee(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Shift Reconciliation", "Dip Reading"],
		non_standard_fieldnames={"Shift Reconciliation": "employee", "Dip Reading": "employee"},
	)


def account(data=None):
	return _extend(
		data,
		group=_("Fuel"),
		items=["Fuel Charge Type"],
		non_standard_fieldnames={"Fuel Charge Type": "default_account"},
	)


def _extend(data, group, items, non_standard_fieldnames=None, internal_links=None):
	data = frappe._dict(data or {})
	data.setdefault("transactions", [])
	data.setdefault("non_standard_fieldnames", {})
	data.setdefault("internal_links", {})

	data["non_standard_fieldnames"].update(non_standard_fieldnames or {})
	data["internal_links"].update(internal_links or {})

	for existing in data["transactions"]:
		if existing.get("label") == group:
			for name in items:
				if name not in existing["items"]:
					existing["items"].append(name)
			return data

	data["transactions"].append({"label": group, "items": list(items)})
	return data
