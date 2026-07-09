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

		from fpms.fuel_pump_management_system.doctype.fuel_credit_sale.fuel_credit_sale import FuelCreditSale
		from fpms.fuel_pump_management_system.doctype.nozzle_reading.nozzle_reading import NozzleReading
		from fpms.fuel_pump_management_system.doctype.shift_payment.shift_payment import ShiftPayment

		amended_from: DF.Link | None
		credit_sales: DF.Table[FuelCreditSale]
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
		total_credit_sales: DF.Currency
		total_fuel_litres: DF.Float
		total_fuel_sales: DF.Currency
		variance_amount: DF.Currency
		variance_status: DF.Literal["Balanced", "Shortage", "Excess"]
	# end: auto-generated types

	def validate(self):
		self.calculate_readings()
		self.calculate_credit_sales()
		self.calculate_totals()
		self.set_variance()
		self.set_status()

	def on_submit(self):
		self.create_credit_invoices()
		self.create_cash_sales_invoice()
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

	def _rate_for(self, item, price_list):
		if not item or not price_list:
			return 0.0
		return get_effective_price(item, price_list, self.shift_date)

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
				row.rate = self._rate_for(row.item, price_list)
			row.sale_amount = flt(row.sale_litres) * flt(row.rate)

	def calculate_credit_sales(self):
		"""Value each on-account fuel sale at the effective-dated price."""
		price_list = self._price_list()
		for row in self.credit_sales:
			if not row.item and row.nozzle:
				row.item = frappe.db.get_value("Nozzle", row.nozzle, "item")
			if row.fuel_card and not row.customer:
				row.customer = frappe.db.get_value("Fuel Card", row.fuel_card, "customer")

			if not row.rate and row.item and price_list:
				row.rate = self._rate_for(row.item, price_list)
			row.amount = flt(row.litres) * flt(row.rate)

	def calculate_totals(self):
		self.total_fuel_litres = sum(flt(r.sale_litres) for r in self.reading_details)
		self.total_fuel_sales = sum(flt(r.sale_amount) for r in self.reading_details)
		self.total_collected = sum(flt(p.amount) for p in self.payment_details)
		self.total_credit_sales = sum(flt(r.amount) for r in self.credit_sales)

	def set_variance(self):
		# Everything dispensed should be either collected (cash/card) or billed on credit.
		accounted = flt(self.total_collected) + flt(self.total_credit_sales)
		self.variance_amount = accounted - flt(self.total_fuel_sales)
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

	# ------------------------------------------------------------------ postings

	def _resolve_customer(self):
		if self.pos_profile:
			cust = frappe.db.get_value("POS Profile", self.pos_profile, "customer")
			if cust:
				return cust
		return frappe.db.get_single_value("Fuel Pump Settings", "default_customer")

	def _new_fuel_invoice(self, customer, update_stock=1):
		invoice = frappe.new_doc("Sales Invoice")
		invoice.customer = customer
		invoice.posting_date = self.shift_date
		invoice.set_posting_time = 1
		invoice.update_stock = update_stock
		invoice.fpms_shift = self.name
		invoice.flags.ignore_permissions = True
		return invoice

	def create_credit_invoices(self):
		"""Bill each credit customer a Sales Invoice on account (posts to their receivable)."""
		if not self.credit_sales:
			return

		by_customer = {}
		for row in self.credit_sales:
			if not row.customer:
				frappe.throw(_("Credit sale row #{0} has no customer.").format(row.idx))
			by_customer.setdefault(row.customer, []).append(row)

		for customer, rows in by_customer.items():
			lines = _group_fuel_lines(rows, litres_field="litres")
			if not lines:
				continue

			invoice = self._new_fuel_invoice(customer)
			invoice.remarks = _("Credit fuel sales for shift {0}").format(self.name)
			_append_fuel_lines(invoice, lines)
			invoice.set_missing_values()
			invoice.insert()
			invoice.submit()

			for row in rows:
				row.db_set("sales_invoice", invoice.name)

	def create_cash_sales_invoice(self):
		"""Invoice the walk-in customer for the cash portion (throughput minus credit litres).

		Fuel is a non-taxable supply, so no tax template is applied. ``update_stock`` on each
		fuel invoice relieves wet-stock from the tank warehouse; the cash and credit invoices
		together relieve exactly the shift's throughput.
		"""
		if self.sales_invoice:
			return

		cash_lines = self._cash_fuel_lines()
		if not cash_lines:
			return

		customer = self._resolve_customer()
		if not customer:
			frappe.msgprint(
				_(
					"No default customer set on the POS Profile or Fuel Pump Settings — "
					"skipping the cash Sales Invoice. Cash-sold wet-stock was not relieved."
				),
				alert=True,
			)
			return

		invoice = self._new_fuel_invoice(customer)
		invoice.remarks = _("Cash fuel sales for shift {0}").format(self.name)
		_append_fuel_lines(invoice, cash_lines)
		invoice.set_missing_values()
		invoice.insert()
		invoice.submit()
		self.db_set("sales_invoice", invoice.name)

	def _cash_fuel_lines(self):
		"""Throughput per (item, warehouse) minus credit litres = the cash-sold portion."""
		throughput = _group_fuel_lines(self.reading_details, litres_field="sale_litres")
		credit = _group_fuel_lines(self.credit_sales, litres_field="litres")

		cash = {}
		for key, data in throughput.items():
			qty = flt(data["qty"]) - flt(credit.get(key, {}).get("qty", 0))
			if qty > 0.0005:
				cash[key] = {"qty": qty, "rate": data["rate"]}
		return cash

	def cancel_linked_documents(self):
		"""Cancel every Sales Invoice this shift created (cash + per-customer credit)."""
		invoices = frappe.get_all(
			"Sales Invoice",
			filters={"fpms_shift": self.name, "docstatus": 1},
			pluck="name",
		)
		for name in invoices:
			inv = frappe.get_doc("Sales Invoice", name)
			inv.flags.ignore_permissions = True
			inv.cancel()


def resolve_warehouse(item, nozzle=None):
	"""Resolve the tank warehouse for a fuel line: nozzle's tank, else any tank for the item."""
	tank = None
	if nozzle:
		tank = frappe.db.get_value("Nozzle", nozzle, "tank")
	if not tank and item:
		tank = frappe.db.get_value("Tank", {"item": item}, "name")
	return frappe.db.get_value("Tank", tank, "warehouse") if tank else None


def _group_fuel_lines(rows, litres_field):
	"""Group rows by (item, tank warehouse), summing litres and keeping the rate."""
	lines = {}
	for row in rows:
		litres = flt(row.get(litres_field))
		if not row.item or litres <= 0:
			continue
		warehouse = resolve_warehouse(row.item, row.get("nozzle"))
		key = (row.item, warehouse)
		bucket = lines.setdefault(key, {"qty": 0.0, "rate": flt(row.rate)})
		bucket["qty"] += litres
	return lines


def _append_fuel_lines(invoice, lines):
	for (item_code, warehouse), data in lines.items():
		invoice.append(
			"items",
			{
				"item_code": item_code,
				"qty": data["qty"],
				"rate": data["rate"],
				"warehouse": warehouse,
			},
		)
