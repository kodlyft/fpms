# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from fpms.events.pricing import get_effective_price


class ShiftReconciliation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from fpms.fuel_pump_management_system.doctype.nozzle_reading.nozzle_reading import NozzleReading
		from fpms.fuel_pump_management_system.doctype.shift_payment.shift_payment import ShiftPayment

		amended_from: DF.Link | None
		employee: DF.Link | None
		naming_series: DF.Literal["FPMS-SHIFT-.YYYY.-"]
		payment_details: DF.Table[ShiftPayment]
		pos_profile: DF.Link | None
		reading_details: DF.Table[NozzleReading]
		sales_invoice: DF.Link | None
		shift_date: DF.Date
		shift_end_time: DF.Time | None
		shift_start_time: DF.Time | None
		shift_type: DF.Link | None
		status: DF.Literal["Draft", "Submitted", "Cancelled"]
		stock_entry: DF.Link | None
		total_collected: DF.Currency
		total_fuel_litres: DF.Float
		total_fuel_sales: DF.Currency
		variance_amount: DF.Currency
		variance_status: DF.Literal["Balanced", "Shortage", "Excess"]
	# end: auto-generated types

	def validate(self):
		self.calculate_readings()
		self.calculate_totals()
		self.set_variance()
		self.set_status()

	def on_submit(self):
		self.create_fuel_sales_invoice()
		self.db_set("status", self._status_value())

	def on_cancel(self):
		self.cancel_linked_documents()
		self.db_set("status", self._status_value())

	def _price_list(self):
		if self.pos_profile:
			pl = frappe.db.get_value("POS Profile", self.pos_profile, "selling_price_list")
			if pl:
				return pl
		return frappe.db.get_single_value("Fuel Pump Settings", "default_price_list")

	def calculate_readings(self):
		"""Compute per-nozzle sale litres and value at the effective-dated price."""
		price_list = self._price_list()
		for row in self.reading_details:
			if not row.item and row.nozzle:
				row.item = frappe.db.get_value("Nozzle", row.nozzle, "item")

			row.sale_litres = flt(row.closing_reading) - flt(row.opening_reading) - flt(row.testing_litres)
			if row.sale_litres < 0:
				frappe.throw(
					_(
						"Row #{0}: closing reading cannot be less than opening plus testing for nozzle {1}."
					).format(row.idx, row.nozzle)
				)

			if not row.rate and row.item and price_list:
				row.rate = get_effective_price(row.item, price_list, self.shift_date)
			row.sale_amount = flt(row.sale_litres) * flt(row.rate)

	def calculate_totals(self):
		self.total_fuel_litres = sum(flt(r.sale_litres) for r in self.reading_details)
		self.total_fuel_sales = sum(flt(r.sale_amount) for r in self.reading_details)
		self.total_collected = sum(flt(p.amount) for p in self.payment_details)

	def set_variance(self):
		self.variance_amount = flt(self.total_collected) - flt(self.total_fuel_sales)
		if abs(self.variance_amount) < 0.005:
			self.variance_status = "Balanced"
		elif self.variance_amount < 0:
			self.variance_status = "Shortage"
		else:
			self.variance_status = "Excess"

	def set_status(self):
		self.status = self._status_value()

	def _status_value(self):
		return {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus]

	def _resolve_customer(self):
		if self.pos_profile:
			cust = frappe.db.get_value("POS Profile", self.pos_profile, "customer")
			if cust:
				return cust
		return frappe.db.get_single_value("Fuel Pump Settings", "default_customer")

	def create_fuel_sales_invoice(self):
		"""Create a non-taxable Sales Invoice for the shift's fuel sales.

		Fuel is a non-taxable supply in Pakistan, so no tax template is applied. The invoice
		is created with ``update_stock=1`` and each line pointed at its tank warehouse, which
		relieves wet-stock in the same posting.
		"""
		if self.sales_invoice or not self.total_fuel_sales:
			return

		customer = self._resolve_customer()
		if not customer:
			frappe.msgprint(
				_(
					"No default customer set on the POS Profile or Fuel Pump Settings — "
					"skipping Sales Invoice creation. Wet-stock was not relieved."
				),
				alert=True,
			)
			return

		lines = self._group_fuel_lines()
		if not lines:
			return

		invoice = frappe.new_doc("Sales Invoice")
		invoice.customer = customer
		invoice.posting_date = self.shift_date
		invoice.update_stock = 1
		invoice.fpms_shift = self.name
		invoice.remarks = _("Fuel sales for shift {0}").format(self.name)
		for key, data in lines.items():
			item_code, warehouse = key
			invoice.append(
				"items",
				{
					"item_code": item_code,
					"qty": data["qty"],
					"rate": data["rate"],
					"warehouse": warehouse,
				},
			)
		invoice.set_missing_values()
		invoice.flags.ignore_permissions = True
		invoice.insert()
		invoice.submit()

		self.db_set("sales_invoice", invoice.name)

	def _group_fuel_lines(self):
		"""Group reading rows by (item, tank warehouse) for the invoice."""
		lines = {}
		for row in self.reading_details:
			if not row.item or flt(row.sale_litres) <= 0:
				continue
			warehouse = None
			if row.nozzle:
				tank = frappe.db.get_value("Nozzle", row.nozzle, "tank")
				if tank:
					warehouse = frappe.db.get_value("Tank", tank, "warehouse")
			key = (row.item, warehouse)
			bucket = lines.setdefault(key, {"qty": 0.0, "rate": flt(row.rate)})
			bucket["qty"] += flt(row.sale_litres)
		return lines

	def cancel_linked_documents(self):
		if self.sales_invoice and frappe.db.exists("Sales Invoice", self.sales_invoice):
			inv = frappe.get_doc("Sales Invoice", self.sales_invoice)
			if inv.docstatus == 1:
				inv.flags.ignore_permissions = True
				inv.cancel()
		if self.stock_entry and frappe.db.exists("Stock Entry", self.stock_entry):
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			if se.docstatus == 1:
				se.flags.ignore_permissions = True
				se.cancel()
