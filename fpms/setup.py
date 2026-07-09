# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

FPMS_ROLES = (
	("FPMS Manager", 1),
	("FPMS Cashier", 1),
	("FPMS Operator", 1),
)

FPMS_CUSTOM_FIELDS = {
	"Sales Invoice": [
		{
			"fieldname": "fpms_shift",
			"label": "FPMS Shift Reconciliation",
			"fieldtype": "Link",
			"options": "Shift Reconciliation",
			"insert_after": "cost_center",
			"read_only": 1,
			"print_hide": 1,
		}
	],
	"POS Invoice": [
		{
			"fieldname": "fpms_shift",
			"label": "FPMS Shift Reconciliation",
			"fieldtype": "Link",
			"options": "Shift Reconciliation",
			"insert_after": "cost_center",
			"read_only": 1,
			"print_hide": 1,
		}
	],
	"Item": [
		{
			"fieldname": "fpms_is_fuel",
			"label": "Is Fuel Product",
			"fieldtype": "Check",
			"insert_after": "is_stock_item",
			"description": "Marks this item as a fuel grade dispensed through nozzles.",
		}
	],
}

FPMS_TAX_TEMPLATES = (
	("Fuel - Zero Rated", 0.0),
	("Standard 18% - Lubricants & C-Store", 18.0),
)


def ensure_roles():
	for role_name, desk_access in FPMS_ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc(
				{
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": desk_access,
				}
			).insert(ignore_permissions=True)


def ensure_custom_fields():
	fields = {dt: defs for dt, defs in FPMS_CUSTOM_FIELDS.items() if frappe.db.exists("DocType", dt)}
	if fields:
		create_custom_fields(fields, ignore_validate=True)


def ensure_tax_templates():
	"""Create split-supply Item Tax Templates for each company (idempotent)."""
	if not frappe.db.exists("DocType", "Item Tax Template"):
		return

	for company in frappe.get_all("Company", pluck="name"):
		for title, rate in FPMS_TAX_TEMPLATES:
			name = f"{title} - {frappe.get_cached_value('Company', company, 'abbr')}"
			if frappe.db.exists("Item Tax Template", name):
				continue

			account = _sales_tax_account(company)
			if not account:
				continue

			doc = frappe.new_doc("Item Tax Template")
			doc.title = title
			doc.company = company
			doc.append("taxes", {"tax_type": account, "tax_rate": rate})
			doc.flags.ignore_permissions = True
			try:
				doc.insert()
			except frappe.DuplicateEntryError:
				pass


def _sales_tax_account(company):
	abbr = frappe.get_cached_value("Company", company, "abbr")
	for candidate in (f"VAT - {abbr}", f"Sales Tax - {abbr}", f"Output Tax - {abbr}"):
		if frappe.db.exists("Account", candidate):
			return candidate
	return frappe.db.get_value("Account", {"company": company, "account_type": "Tax", "is_group": 0}, "name")


def before_install():
	ensure_roles()


def after_install():
	ensure_roles()
	ensure_custom_fields()
	ensure_tax_templates()


def after_migrate():
	ensure_roles()
	ensure_custom_fields()
