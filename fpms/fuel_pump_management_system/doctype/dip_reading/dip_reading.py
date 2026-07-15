# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class DipReading(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		book_stock: DF.Float
		density: DF.Float
		dip_mm: DF.Float
		employee: DF.Link | None
		item: DF.Link | None
		naming_series: DF.Literal["FPMS-DIP-.YYYY.-"]
		reading_datetime: DF.Datetime
		status: DF.Literal["Draft", "Submitted", "Cancelled"]
		stock_reconciliation: DF.Link | None
		tank: DF.Link
		temperature: DF.Float
		variance_litres: DF.Float
		variance_pct: DF.Percent
		volume_litres: DF.Float
		water_dip_mm: DF.Float
		within_tolerance: DF.Check
	# end: auto-generated types

	def validate(self):
		self.set_volume()
		self.set_book_stock()
		self.set_variance()
		self.set_status()

	def on_submit(self):
		self.maybe_create_stock_reconciliation()
		self.db_set("status", self._status_value())

	def on_cancel(self):
		self.cancel_stock_reconciliation()
		self.db_set("status", self._status_value())

	def set_volume(self):
		tank = frappe.get_cached_doc("Tank", self.tank)
		self.item = tank.item
		self.volume_litres = tank.interpolate_volume(self.dip_mm)

	def set_book_stock(self):
		warehouse = frappe.db.get_value("Tank", self.tank, "warehouse")
		self.book_stock = get_book_stock(self.item, warehouse)

	def set_variance(self):
		self.variance_litres = flt(self.volume_litres) - flt(self.book_stock)
		self.variance_pct = (self.variance_litres / self.book_stock * 100) if self.book_stock else 0.0

		threshold = flt(frappe.db.get_single_value("Fuel Pump Settings", "variance_threshold_pct")) or 0.5
		self.within_tolerance = 1 if abs(self.variance_pct) <= threshold else 0
		if not self.within_tolerance:
			frappe.msgprint(
				_(
					"Dip variance {0}% exceeds the {1}% tolerance. Investigate for leak or short delivery."
				).format(flt(self.variance_pct, 2), threshold),
				alert=True,
				indicator="orange",
			)

	def set_status(self):
		self.status = self._status_value()

	def _status_value(self):
		return {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus]

	def maybe_create_stock_reconciliation(self):
		if self.stock_reconciliation:
			return
		if not frappe.db.get_single_value("Fuel Pump Settings", "auto_stock_reconcile"):
			return
		if abs(flt(self.variance_litres)) < 0.005:
			return

		warehouse = frappe.db.get_value("Tank", self.tank, "warehouse")
		recon = frappe.new_doc("Stock Reconciliation")
		recon.purpose = "Stock Reconciliation"
		recon.posting_date = frappe.utils.getdate(self.reading_datetime)
		recon.set_posting_time = 1
		recon.append(
			"items",
			{
				"item_code": self.item,
				"warehouse": warehouse,
				"qty": self.volume_litres,
				"valuation_rate": get_valuation_rate(self.item, warehouse),
			},
		)
		recon.flags.ignore_permissions = True
		recon.insert()
		recon.submit()
		self.db_set("stock_reconciliation", recon.name)

	def cancel_stock_reconciliation(self):
		if self.stock_reconciliation and frappe.db.exists("Stock Reconciliation", self.stock_reconciliation):
			recon = frappe.get_doc("Stock Reconciliation", self.stock_reconciliation)
			if recon.docstatus == 1:
				recon.flags.ignore_permissions = True
				recon.cancel()


def get_book_stock(item_code: str, warehouse: str) -> float:
	"""Return the current book stock (Bin actual_qty) for an item in a warehouse."""
	if not item_code or not warehouse:
		return 0.0
	qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
	return flt(qty)


def get_valuation_rate(item_code: str, warehouse: str) -> float:
	rate = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "valuation_rate")
	if not rate:
		rate = frappe.db.get_value("Item", item_code, "valuation_rate")
	return flt(rate)
