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

_SKIP_LEVIES_FIELD = {
	"fieldname": "fpms_skip_levies",
	"label": "Skip FPMS Fuel Levies",
	"fieldtype": "Check",
	"insert_after": "taxes_and_charges",
	"print_hide": 1,
	"description": "Do not add the fuel levies configured in Fuel Pump Settings to this document.",
}

for _purchase_doctype in ("Purchase Order", "Purchase Receipt", "Purchase Invoice"):
	FPMS_CUSTOM_FIELDS[_purchase_doctype] = [dict(_SKIP_LEVIES_FIELD)]

FPMS_TAX_TEMPLATES = (
	("Fuel - Zero Rated", 0.0),
	("Standard 18% - Lubricants & C-Store", 18.0),
)

FPMS_CHARGE_TYPES = (
	"Dealer Commission",
	"OMC Margin",
	"Petroleum Development Levy",
	"Climate Support Levy",
	"Sales Tax",
	"Customs Duty",
	"Inland Freight Equalisation Margin",
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


def ensure_charge_types():
	"""Seed the standard Fuel Charge Types and adopt any values already used on rows."""
	if not frappe.db.exists("DocType", "Fuel Charge Type"):
		return

	meta = frappe.get_meta("Fuel Charge Type")
	company_field = meta.get_field("company")
	default_company = None
	if company_field:
		default_company = frappe.db.get_single_value(
			"Fuel Pump Settings", "default_company"
		) or frappe.db.get_value("Company", {}, "name")
		if company_field.reqd and default_company:
			for name in frappe.get_all(
				"Fuel Charge Type", filters={"company": ["is", "not set"]}, pluck="name"
			):
				frappe.db.set_value("Fuel Charge Type", name, "company", default_company)

	names = set(FPMS_CHARGE_TYPES)
	for child in ("Fuel Price Component", "Fuel Purchase Charge"):
		if frappe.db.has_column(child, "component"):
			names.update(
				frappe.db.sql_list(
					f"SELECT DISTINCT component FROM `tab{child}` WHERE component IS NOT NULL AND component != ''"
				)
			)

	for name in names:
		if not frappe.db.exists("Fuel Charge Type", name):
			doc = frappe.new_doc("Fuel Charge Type")
			doc.charge_type = name
			if company_field and default_company:
				doc.company = default_company
			doc.insert(ignore_permissions=True)


def ensure_charge_accounts():
	"""
	Give every Fuel Charge Type its own levy account.

	The levy accounts are credited when fuel is received and debited back when the OMC's
	invoice is booked, so they net to zero. They exist to expose what each litre of the
	ex-depot price was made of. ERPNext keys the per-litre rate of a tax row by its account,
	so two levies can never share one.
	"""
	if not frappe.db.exists("DocType", "Fuel Charge Type"):
		return

	parents = {}
	for charge in frappe.get_all(
		"Fuel Charge Type", filters={"default_account": ["is", "not set"]}, fields=["name", "company"]
	):
		if not charge.company:
			continue

		if charge.company not in parents:
			parents[charge.company] = _levy_parent_account(charge.company)
		parent = parents[charge.company]
		if not parent:
			continue

		account = _create_levy_account(charge.name, charge.company, parent)
		if account:
			frappe.db.set_value("Fuel Charge Type", charge.name, "default_account", account)


def _create_levy_account(charge_type, company, parent):
	abbr = frappe.get_cached_value("Company", company, "abbr")
	name = f"{charge_type} - {abbr}"

	if frappe.db.exists("Account", name):
		return name if not frappe.db.get_value("Account", name, "is_group") else None

	doc = frappe.new_doc("Account")
	doc.account_name = charge_type
	doc.company = company
	doc.parent_account = parent
	doc.account_type = "Expenses Included In Valuation"
	doc.flags.ignore_permissions = True
	doc.insert()
	return doc.name


def _levy_parent_account(company):
	abbr = frappe.get_cached_value("Company", company, "abbr")
	name = f"Fuel Levies - {abbr}"
	if frappe.db.exists("Account", name):
		return name

	parent = None
	for candidate in (f"Stock Expenses - {abbr}", f"Indirect Expenses - {abbr}", f"Expenses - {abbr}"):
		if frappe.db.get_value("Account", candidate, "is_group"):
			parent = candidate
			break

	if not parent:
		parent = frappe.db.get_value(
			"Account",
			{"company": company, "root_type": "Expense", "is_group": 1, "parent_account": ["is", "not set"]},
			"name",
		)
	if not parent:
		return None

	doc = frappe.new_doc("Account")
	doc.account_name = "Fuel Levies"
	doc.company = company
	doc.parent_account = parent
	doc.is_group = 1
	doc.flags.ignore_permissions = True
	doc.insert()
	return doc.name


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
	ensure_charge_types()
	ensure_charge_accounts()
	ensure_tax_templates()


def after_migrate():
	ensure_roles()
	ensure_custom_fields()
	ensure_charge_types()
	ensure_charge_accounts()
