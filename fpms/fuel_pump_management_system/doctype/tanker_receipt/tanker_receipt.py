# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from fpms.events.pricing import get_effective_ex_depot


class TankerReceipt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from fpms.fuel_pump_management_system.doctype.fuel_purchase_charge.fuel_purchase_charge import (
			FuelPurchaseCharge,
		)

		amended_from: DF.Link | None
		amount: DF.Currency
		bol_litres: DF.Float
		charges: DF.Table[FuelPurchaseCharge]
		company: DF.Link
		density: DF.Float
		dip_after_mm: DF.Float
		dip_before_mm: DF.Float
		driver_name: DF.Data | None
		item: DF.Link | None
		naming_series: DF.Literal["FPMS-TANKER-.YYYY.-"]
		posting_date: DF.Date
		purchase_order: DF.Link | None
		purchase_receipt: DF.Link | None
		rate: DF.Currency
		received_litres: DF.Float
		shortfall_litres: DF.Float
		status: DF.Literal["Draft", "Submitted", "Cancelled"]
		supplier: DF.Link
		tank: DF.Link
		temperature: DF.Float
		total_charges: DF.Currency
		vehicle_number: DF.Data | None
		volume_after: DF.Float
		volume_before: DF.Float
	# end: auto-generated types

	def validate(self):
		self.set_quantities()
		self.set_valuation()
		self.set_charges()
		self.set_status()

	def on_submit(self):
		self.create_purchase_receipt()
		self.db_set("status", self._status_value())

	def on_cancel(self):
		self.cancel_purchase_receipt()
		self.db_set("status", self._status_value())

	def set_quantities(self):
		tank = frappe.get_cached_doc("Tank", self.tank)
		self.item = tank.item
		self.volume_before = tank.interpolate_volume(self.dip_before_mm)
		self.volume_after = tank.interpolate_volume(self.dip_after_mm)
		self.received_litres = flt(self.volume_after) - flt(self.volume_before)
		self.shortfall_litres = flt(self.bol_litres) - flt(self.received_litres)

		if self.received_litres < 0:
			frappe.throw(_("Dip after decantation cannot be lower than dip before."))

	def set_valuation(self):
		"""Default the purchase rate so the receipt never values stock at zero."""
		if not self.rate:
			self.rate = self._default_rate()
		self.amount = flt(self.received_litres) * flt(self.rate)

	def _default_rate(self):
		if self.purchase_order and self.item:
			po_rate = frappe.db.get_value(
				"Purchase Order Item",
				{"parent": self.purchase_order, "item_code": self.item},
				"rate",
			)
			if po_rate:
				return flt(po_rate)
		ex_depot = get_effective_ex_depot(self.item, self.posting_date)
		if ex_depot:
			return ex_depot
		return flt(frappe.db.get_value("Item", self.item, "last_purchase_rate")) or flt(
			frappe.db.get_value("Item", self.item, "valuation_rate")
		)

	def set_charges(self):
		"""Track the levies/charges embedded in this purchase (does not change valuation).

		If left blank, seed the rows from the default purchase charges configured in Fuel Pump
		Settings; then value each row for the received quantity.
		"""
		if not self.charges:
			for default in frappe.get_all(
				"Fuel Price Component",
				filters={"parenttype": "Fuel Pump Settings", "parentfield": "default_purchase_charges"},
				fields=["component", "rate_per_litre", "account"],
				order_by="idx asc",
			):
				self.append(
					"charges",
					{
						"component": default.component,
						"rate_per_litre": default.rate_per_litre,
						"account": default.account,
					},
				)

		for row in self.charges:
			row.amount = flt(row.rate_per_litre) * flt(self.received_litres)
		self.total_charges = sum(flt(row.amount) for row in self.charges)

	def set_status(self):
		self.status = self._status_value()

	def _status_value(self):
		return {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus]

	def create_purchase_receipt(self):
		"""
		Create a Purchase Receipt for the dip-verified received quantity.

		The purchase rate is set explicitly so fuel never enters stock at zero valuation
		(which would corrupt COGS on every subsequent sale).
		"""
		if self.purchase_receipt or flt(self.received_litres) <= 0:
			return

		if flt(self.rate) <= 0:
			frappe.throw(_("Set a Purchase Rate / Litre so the received fuel is valued correctly."))

		warehouse = frappe.db.get_value("Tank", self.tank, "warehouse")
		if self.purchase_order:
			pr = self._purchase_receipt_from_po(warehouse)
		else:
			pr = self._standalone_purchase_receipt(warehouse)

		pr.set_missing_values()
		pr.flags.ignore_permissions = True
		pr.insert()
		pr.submit()

		self.db_set("purchase_receipt", pr.name)

		if abs(flt(self.shortfall_litres)) >= 1:
			frappe.msgprint(
				_("Delivery shortfall of {0} litres recorded against BOL.").format(
					flt(self.shortfall_litres, 3)
				),
				alert=True,
				indicator="orange",
			)

	def _standalone_purchase_receipt(self, warehouse):
		pr = frappe.new_doc("Purchase Receipt")
		pr.company = self.company
		pr.supplier = self.supplier
		pr.posting_date = self.posting_date
		pr.set_posting_time = 1
		pr.append(
			"items",
			{
				"item_code": self.item,
				"qty": self.received_litres,
				"rate": self.rate,
				"warehouse": warehouse,
			},
		)
		return pr

	def _purchase_receipt_from_po(self, warehouse):
		"""Receive against the linked Purchase Order so it updates and closes cleanly."""
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

		pr = make_purchase_receipt(self.purchase_order)
		pr.company = self.company
		pr.posting_date = self.posting_date
		pr.set_posting_time = 1

		rows = [d for d in pr.items if d.item_code == self.item]
		if not rows:
			frappe.throw(
				_("Purchase Order {0} does not contain the tank's fuel item {1}.").format(
					self.purchase_order, self.item
				)
			)
		row = rows[0]
		row.qty = self.received_litres
		row.rate = self.rate
		row.warehouse = warehouse
		row.idx = 1
		pr.items = [row]
		return pr

	def cancel_purchase_receipt(self):
		if self.purchase_receipt and frappe.db.exists("Purchase Receipt", self.purchase_receipt):
			pr = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
			if pr.docstatus == 1:
				pr.flags.ignore_permissions = True
				pr.cancel()


@frappe.whitelist()
def make_tanker_receipt(source_name: str, target_doc: str | dict | None = None):
	"""Map a Purchase Order to a new Tanker Receipt (Create > Tanker Receipt on the PO)."""
	from frappe.model.mapper import get_mapped_doc

	def post_process(source, target):
		target.purchase_order = source.name
		for item in source.items:
			tank = frappe.db.get_value("Tank", {"item": item.item_code}, "name")
			if tank:
				target.tank = tank
				target.bol_litres = item.qty
				target.rate = item.rate
				break

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
