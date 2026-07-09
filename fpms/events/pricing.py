# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

"""
Effective-dated fuel pricing helpers.

Fuel prices in Pakistan are OGRA-notified ceilings that change fortnightly (sometimes
weekly). We publish each notified price as a dated ERPNext ``Item Price`` (``valid_from``)
and resolve the price effective on a given date here.

We deliberately do NOT rely on ERPNext Pricing Rules, whose ``valid_upto`` is not always
enforced (frappe/erpnext#50122). Dated ``Item Price`` rows are the single source of truth.
"""

import frappe
from frappe.utils import getdate, nowdate


def get_effective_price(item_code: str, price_list: str, on_date=None) -> float:
	"""Return the selling price for ``item_code`` on ``price_list`` effective on ``on_date``.

	Picks the Item Price with the latest ``valid_from`` that is on or before ``on_date``.
	Returns ``0.0`` when no applicable price exists.
	"""
	if not item_code or not price_list:
		return 0.0

	on_date = getdate(on_date or nowdate())

	rows = frappe.get_all(
		"Item Price",
		filters={
			"item_code": item_code,
			"price_list": price_list,
			"selling": 1,
		},
		or_filters=[
			["valid_from", "<=", on_date],
			["valid_from", "is", "not set"],
		],
		fields=["price_list_rate", "valid_from"],
		order_by="valid_from desc",
		limit=1,
	)
	return float(rows[0].price_list_rate) if rows else 0.0


def clear_price_cache(doc, method=None):
	"""Hooked on ``Item Price`` update — placeholder for future price caching."""
	frappe.cache().delete_value("fpms_effective_price")
