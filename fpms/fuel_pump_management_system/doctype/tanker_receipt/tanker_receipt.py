# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from fpms.events.pricing import get_effective_ex_depot
from fpms.events.purchase_taxes import apply_charges, levy_accounts


class TankerReceipt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from fpms.fuel_pump_management_system.doctype.fuel_purchase_charge.fuel_purchase_charge import (
			FuelPurchaseCharge,
		)
		from fpms.fuel_pump_management_system.doctype.tanker_receipt_item.tanker_receipt_item import (
			TankerReceiptItem,
		)

		amended_from: DF.Link | None
		charges: DF.Table[FuelPurchaseCharge]
		company: DF.Link
		driver_name: DF.Data | None
		items: DF.Table[TankerReceiptItem]
		naming_series: DF.Literal["FPMS-TANKER-.YYYY.-"]
		posting_date: DF.Date
		purchase_invoice: DF.Link | None
		purchase_order: DF.Link | None
		purchase_receipt: DF.Link | None
		status: DF.Literal["Draft", "Submitted", "Cancelled"]
		supplier: DF.Link
		total_amount: DF.Currency
		total_bol_litres: DF.Float
		total_charges: DF.Currency
		total_received_litres: DF.Float
		total_shortfall_litres: DF.Float
		vehicle_number: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.set_items()
		self.set_totals()
		self.set_charges()
		self.set_status()

	def on_submit(self):
		self.create_purchase_receipt()
		self.db_set("status", self._status_value())

	def on_cancel(self):
		self.cancel_purchase_receipt()
		self.db_set("status", self._status_value())

	def set_items(self):
		"""Dip-verify and value each product row. A row is never valued at zero cost."""
		for row in self.items:
			tank = frappe.get_cached_doc("Tank", row.tank)
			row.item = tank.item
			row.volume_before = tank.interpolate_volume(row.dip_before_mm)
			row.volume_after = tank.interpolate_volume(row.dip_after_mm)
			row.received_litres = flt(row.volume_after) - flt(row.volume_before)
			row.shortfall_litres = flt(row.bol_litres) - flt(row.received_litres)

			if row.received_litres < 0:
				frappe.throw(
					_("Row #{0}: dip after decantation cannot be lower than dip before.").format(row.idx)
				)

			if not row.rate:
				row.rate = self._default_rate(row.item)
			row.amount = flt(row.received_litres) * flt(row.rate)

	def _default_rate(self, item):
		if self.purchase_order and item:
			po_rate = frappe.db.get_value(
				"Purchase Order Item",
				{"parent": self.purchase_order, "item_code": item},
				"rate",
			)
			if po_rate:
				return flt(po_rate)
		ex_depot = get_effective_ex_depot(item, self.posting_date)
		if ex_depot:
			return ex_depot
		return flt(frappe.db.get_value("Item", item, "last_purchase_rate")) or flt(
			frappe.db.get_value("Item", item, "valuation_rate")
		)

	def set_totals(self):
		self.total_bol_litres = sum(flt(r.bol_litres) for r in self.items)
		self.total_received_litres = sum(flt(r.received_litres) for r in self.items)
		self.total_shortfall_litres = sum(flt(r.shortfall_litres) for r in self.items)
		self.total_amount = sum(flt(r.amount) for r in self.items)

	def set_charges(self):
		"""Record the levies embedded in this purchase, per fuel item.

		They are carried onto the Purchase Receipt as inclusive taxes, so they report what
		each litre of the ex-depot price was made of without changing what is owed or how the
		fuel is valued.
		"""
		received_by_item = {}
		for row in self.items:
			received_by_item[row.item] = received_by_item.get(row.item, 0.0) + flt(row.received_litres)

		if not self.charges and self.purchase_order:
			self._seed_charges_from_purchase_order(received_by_item)
		if not self.charges:
			self._seed_charges_from_settings(received_by_item)

		for row in self.charges:
			litres = received_by_item.get(row.item, self.total_received_litres)
			row.amount = flt(row.rate_per_litre) * flt(litres)
		self.total_charges = sum(flt(row.amount) for row in self.charges)

	def _seed_charges_from_purchase_order(self, received_by_item):
		"""Recover the ordered levies from the tax map ERPNext stored on the ordered items.

		The map holds each levy as a percentage of the levy-exclusive rate, so multiplying it
		back out by that rate returns the rupees per litre the order was placed at.
		"""
		components = levy_accounts(self.company)
		rows = frappe.get_all(
			"Purchase Order Item",
			filters={"parent": self.purchase_order},
			fields=["item_code", "item_tax_rate", "net_rate"],
			order_by="idx asc",
		)

		seen = set()
		for row in rows:
			if row.item_code not in received_by_item:
				continue
			for account, percentage in json.loads(row.item_tax_rate or "{}").items():
				component = components.get(account)
				rate_per_litre = flt(flt(percentage) / 100 * flt(row.net_rate), 3)
				if not component or not rate_per_litre or (row.item_code, component) in seen:
					continue
				seen.add((row.item_code, component))
				self.append(
					"charges",
					{
						"item": row.item_code,
						"component": component,
						"rate_per_litre": rate_per_litre,
						"account": account,
					},
				)

	def _seed_charges_from_settings(self, received_by_item):
		defaults = frappe.get_all(
			"Fuel Price Component",
			filters={"parenttype": "Fuel Pump Settings", "parentfield": "default_purchase_charges"},
			fields=["component", "rate_per_litre", "account"],
			order_by="idx asc",
		)
		for item in received_by_item:
			for default in defaults:
				self.append(
					"charges",
					{
						"item": item,
						"component": default.component,
						"rate_per_litre": default.rate_per_litre,
						"account": default.account,
					},
				)

	def set_status(self):
		self.status = self._status_value()

	def _status_value(self):
		return {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus]

	def create_purchase_receipt(self):
		"""Create a Purchase Receipt for the dip-verified quantities (one line per product).

		Each line's rate is set explicitly so fuel never enters stock at zero valuation.
		"""
		if self.purchase_receipt or flt(self.total_received_litres) <= 0:
			return

		for row in self.items:
			if flt(row.received_litres) > 0 and flt(row.rate) <= 0:
				frappe.throw(
					_("Row #{0}: set a Rate / Litre so the received fuel is valued correctly.").format(
						row.idx
					)
				)

		if self.purchase_order:
			pr = self._purchase_receipt_from_po()
		else:
			pr = self._standalone_purchase_receipt()

		pr.set_missing_values()
		apply_charges(pr, self.charges)
		pr.flags.ignore_permissions = True
		pr.insert()
		pr.submit()

		self.db_set("purchase_receipt", pr.name)

		if abs(flt(self.total_shortfall_litres)) >= 1:
			frappe.msgprint(
				_("Delivery shortfall of {0} litres recorded against BOL.").format(
					flt(self.total_shortfall_litres, 3)
				),
				alert=True,
				indicator="orange",
			)

	def _standalone_purchase_receipt(self):
		pr = frappe.new_doc("Purchase Receipt")
		pr.company = self.company
		pr.supplier = self.supplier
		pr.posting_date = self.posting_date
		pr.set_posting_time = 1
		for row in self.items:
			if flt(row.received_litres) <= 0:
				continue
			pr.append(
				"items",
				{
					"item_code": row.item,
					"qty": row.received_litres,
					"rate": row.rate,
					"warehouse": _tank_warehouse(row.tank),
				},
			)
		return pr

	def _purchase_receipt_from_po(self):
		"""Receive against the linked Purchase Order so it updates and closes cleanly."""
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

		pr = make_purchase_receipt(self.purchase_order)
		pr.company = self.company
		pr.posting_date = self.posting_date
		pr.set_posting_time = 1

		available = list(pr.items)
		kept = []
		for row in self.items:
			if flt(row.received_litres) <= 0:
				continue
			match = next((d for d in available if d.item_code == row.item and d not in kept), None)
			if not match:
				frappe.throw(
					_("Purchase Order {0} does not contain the fuel item {1} (row #{2}).").format(
						self.purchase_order, row.item, row.idx
					)
				)
			match.qty = row.received_litres
			match.rate = row.rate
			match.warehouse = _tank_warehouse(row.tank)
			kept.append(match)

		for idx, item in enumerate(kept, start=1):
			item.idx = idx
		pr.items = kept
		return pr

	def cancel_purchase_receipt(self):
		if self.purchase_receipt and frappe.db.exists("Purchase Receipt", self.purchase_receipt):
			pr = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
			if pr.docstatus == 1:
				pr.flags.ignore_permissions = True
				pr.cancel()


def _tank_warehouse(tank):
	return frappe.db.get_value("Tank", tank, "warehouse") if tank else None


@frappe.whitelist()
def make_tanker_receipt(source_name: str, target_doc: str | dict | None = None):
	"""Map a Purchase Order to a new Tanker Receipt (Create > Tanker Receipt on the PO).

	Every ordered fuel item that maps to a tank becomes an item row, so a single PO covering
	Petrol and Diesel produces one Tanker Receipt with a row per product.
	"""
	from frappe.model.mapper import get_mapped_doc

	def post_process(source, target):
		target.purchase_order = source.name
		for item in source.items:
			tank = frappe.db.get_value("Tank", {"item": item.item_code}, "name")
			if not tank:
				continue
			target.append(
				"items",
				{
					"tank": tank,
					"item": item.item_code,
					"bol_litres": item.qty,
					"rate": item.rate,
				},
			)

	return get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Tanker Receipt",
				"field_map": {"company": "company", "supplier": "supplier"},
				"validation": {"docstatus": ["=", 1]},
			}
		},
		target_doc,
		post_process,
	)
