# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt

TEMPLATE_TITLE = "Fuel Levies"
DEFAULT_CATEGORY = "Valuation and Total"

ALLOWED_ACCOUNT_TYPES = ("Tax", "Chargeable", "Expense Account", "Expenses Included In Valuation")


def apply_fuel_levies(doc, method: str | None = None) -> None:
	"""
	``before_validate`` hook for Purchase Order / Purchase Receipt / Purchase Invoice.
	"""
	if doc.get("fpms_skip_levies") or doc.get("is_return"):
		return

	settings = frappe.get_cached_doc("Fuel Pump Settings")
	if not settings.apply_fuel_levies_on_purchase:
		return

	apply_charges(doc, settings.default_purchase_charges, replace=False)


def apply_charges(doc, charges, replace: bool = True) -> None:
	"""
	Write ``charges`` onto ``doc`` as inclusive Purchase Taxes and Charges rows.

	``charges`` is any iterable of rows exposing ``component``, ``rate_per_litre`` and
	optionally ``item`` and ``account``. Both Fuel Price Component and Fuel Purchase Charge
	qualify. A charge with no ``item`` applies to every fuel grade on the document. When
	``replace`` is false, tax rows that already exist for a levy account are left untouched.
	"""
	company = doc.get("company")
	if not company or not doc.get("items"):
		return

	resolved = _resolve_charges(charges, company)
	if not resolved:
		return

	rates = _item_rates(doc)
	if not rates:
		return

	accounts = list(dict.fromkeys(charge["account"] for charge in resolved))
	existing = {row.account_head: row for row in doc.get("taxes") or []}
	if not replace and all(account in existing for account in accounts):
		return

	percentages = _percentages_by_item(resolved, rates, accounts)
	cost_center = frappe.get_cached_value("Company", company, "cost_center")

	for charge in resolved:
		row = existing.get(charge["account"])
		if row and not replace:
			continue
		if row is None:
			row = doc.append("taxes", {})
			existing[charge["account"]] = row

		row.charge_type = "On Net Total"
		row.account_head = charge["account"]
		row.description = charge["description"]
		row.rate = 0
		row.included_in_print_rate = 1 if charge["included_in_rate"] else 0
		row.category = charge["category"]
		row.add_deduct_tax = "Add"
		row.cost_center = row.cost_center or cost_center

	for item_code, item_percentages in percentages.items():
		template = ensure_item_tax_template(company, item_code, item_percentages)
		for row in doc.get("items"):
			if row.item_code == item_code:
				row.item_tax_template = template


def ensure_item_tax_template(company: str, item_code: str, percentages: dict[str, float]) -> str:
	"""
	Create or refresh the ``Fuel Levies - <item>`` template holding this grade's levy rates.

	The template is rewritten from the document being saved, before ERPNext reads it, so it
	always reflects the rate on that document. It is a shared master only in the sense that
	the same name is reused; submitted documents keep their own ``item_tax_rate`` snapshot.
	"""
	title = f"{TEMPLATE_TITLE} - {item_code}"
	abbr = frappe.get_cached_value("Company", company, "abbr")
	name = f"{title} - {abbr}"

	if frappe.db.exists("Item Tax Template", name):
		template = frappe.get_doc("Item Tax Template", name)
	else:
		template = frappe.new_doc("Item Tax Template")
		template.title = title
		template.company = company

	current = {row.tax_type: flt(row.tax_rate) for row in template.taxes}
	if template.is_new() or current != percentages:
		template.set("taxes", [])
		for account, rate in percentages.items():
			template.append("taxes", {"tax_type": account, "tax_rate": rate})
		template.disabled = 0
		template.flags.ignore_permissions = True
		template.save()

	_ensure_item_tax_link(item_code, template.name)
	return template.name


def _ensure_item_tax_link(item_code: str, template: str) -> None:
	"""Keep the levy template in the Item's own tax table when that table is in use.

	ERPNext replaces an item row's template with the item's first valid one whenever the Item
	has any tax rows at all, which would silently zero the levies. Items with an empty tax
	table are left alone so a default install stays clean.
	"""
	item = frappe.get_doc("Item", item_code)
	if not item.taxes or any(row.item_tax_template == template for row in item.taxes):
		return

	item.append("taxes", {"item_tax_template": template})
	item.flags.ignore_permissions = True
	item.flags.ignore_mandatory = True
	item.save()


def levy_accounts(company: str) -> dict[str, str]:
	"""Return ``{account: charge type}`` for every enabled levy of ``company``."""
	rows = frappe.get_all(
		"Fuel Charge Type",
		filters={"company": company, "disabled": 0},
		fields=["name", "default_account"],
	)
	return {row.default_account: row.name for row in rows if row.default_account}


def rate_precision() -> int:
	"""The precision ERPNext rounds a tax rate to before using it."""
	field = frappe.get_meta("Purchase Taxes and Charges").get_field("rate")
	return cint(field.precision) or cint(frappe.db.get_default("float_precision")) or 3


def _percentages_by_item(resolved, rates: dict[str, float], accounts) -> dict[str, dict[str, float]]:
	"""Convert each per-litre levy into a percentage of the grade's levy-exclusive rate.

	Every fuel grade carries a rate for every levy account. An explicit zero where the levy
	does not apply, because otherwise ERPNext would fall back to the header rate.
	"""
	precision = rate_precision()
	percentages = {item_code: dict.fromkeys(accounts, 0.0) for item_code in rates}

	for item_code, item_rate in rates.items():
		applicable = [c for c in resolved if not c["item"] or c["item"] == item_code]
		embedded = sum(c["rate"] for c in applicable if c["included_in_rate"])
		net_rate = item_rate - embedded
		if net_rate <= 0:
			frappe.throw(
				_(
					"Levies of {0} per litre are embedded in {1}, which leaves nothing of its rate {2}."
				).format(frappe.bold(embedded), frappe.bold(item_code), frappe.bold(item_rate))
			)

		for charge in applicable:
			percentages[item_code][charge["account"]] += flt(charge["rate"] / net_rate * 100, precision)

	return percentages


def _resolve_charges(charges, company: str) -> list[dict]:
	resolved = []
	seen_accounts = {}

	for row in charges or []:
		component = row.get("component")
		if not component:
			continue

		charge_type = frappe.get_cached_doc("Fuel Charge Type", component)
		if charge_type.disabled:
			continue

		account = row.get("account") or charge_type.default_account
		if not account:
			frappe.throw(
				_("Set a Levy Account on Fuel Charge Type {0} before using it on a purchase.").format(
					frappe.bold(component)
				)
			)

		if seen_accounts.setdefault(account, component) != component:
			frappe.throw(
				_(
					"Fuel Charge Types {0} and {1} share the levy account {2}. Give each levy its own account so its rate can be tracked separately."
				).format(frappe.bold(seen_accounts[account]), frappe.bold(component), frappe.bold(account))
			)

		_validate_account(account, company, component)
		resolved.append(
			{
				"account": account,
				"description": component,
				"rate": flt(row.get("rate_per_litre")),
				"item": row.get("item"),
				"category": charge_type.category or DEFAULT_CATEGORY,
				"included_in_rate": charge_type.included_in_rate,
			}
		)

	return resolved


def _validate_account(account: str, company: str, component: str) -> None:
	account_type, account_company, is_group = frappe.get_cached_value(
		"Account", account, ["account_type", "company", "is_group"]
	)
	if is_group:
		frappe.throw(_("Levy account {0} is a group account.").format(frappe.bold(account)))
	if account_company != company:
		frappe.throw(
			_("Levy account {0} on Fuel Charge Type {1} does not belong to {2}.").format(
				frappe.bold(account), frappe.bold(component), frappe.bold(company)
			)
		)
	if account_type not in ALLOWED_ACCOUNT_TYPES:
		frappe.throw(
			_("Levy account {0} must be of type {1}, not {2}.").format(
				frappe.bold(account),
				", ".join(ALLOWED_ACCOUNT_TYPES),
				frappe.bold(account_type or _("None")),
			)
		)


def _item_rates(doc) -> dict[str, float]:
	"""Return ``{fuel item: rate}`` for the fuel grades on ``doc`` that carry a rate."""
	fuel_items = _fuel_item_codes(doc)
	rates = {}
	for row in doc.get("items") or []:
		if row.item_code in fuel_items and flt(row.rate) > 0:
			rates.setdefault(row.item_code, flt(row.rate))
	return rates


def _fuel_item_codes(doc) -> set[str]:
	codes = {row.item_code for row in doc.get("items") or [] if row.get("item_code")}
	if not codes:
		return set()

	fuel = set(frappe.get_all("Tank", filters={"item": ["in", list(codes)]}, pluck="item"))
	if frappe.db.has_column("Item", "fpms_is_fuel"):
		fuel.update(
			frappe.get_all("Item", filters={"name": ["in", list(codes)], "fpms_is_fuel": 1}, pluck="name")
		)
	return fuel & codes
