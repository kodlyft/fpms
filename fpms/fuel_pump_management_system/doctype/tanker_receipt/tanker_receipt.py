# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class TankerReceipt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		bol_litres: DF.Float
		density: DF.Float
		dip_after_mm: DF.Float
		dip_before_mm: DF.Float
		driver_name: DF.Data | None
		item: DF.Link | None
		naming_series: DF.Literal["FPMS-TANKER-.YYYY.-"]
		posting_date: DF.Date
		purchase_order: DF.Link | None
		purchase_receipt: DF.Link | None
		received_litres: DF.Float
		shortfall_litres: DF.Float
		status: DF.Literal["Draft", "Submitted", "Cancelled"]
		supplier: DF.Link
		tank: DF.Link
		temperature: DF.Float
		vehicle_number: DF.Data | None
		volume_after: DF.Float
		volume_before: DF.Float
	# end: auto-generated types

	def validate(self):
		self.set_quantities()
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

	def set_status(self):
		self.status = self._status_value()

	def _status_value(self):
		return {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus]

	def create_purchase_receipt(self):
		"""Create a Purchase Receipt for the dip-verified received quantity."""
		if self.purchase_receipt or flt(self.received_litres) <= 0:
			return

		warehouse = frappe.db.get_value("Tank", self.tank, "warehouse")
		pr = frappe.new_doc("Purchase Receipt")
		pr.supplier = self.supplier
		pr.posting_date = self.posting_date
		pr.set_posting_time = 1
		pr.append(
			"items",
			{
				"item_code": self.item,
				"qty": self.received_litres,
				"warehouse": warehouse,
				"purchase_order": self.purchase_order,
			},
		)
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

	def cancel_purchase_receipt(self):
		if self.purchase_receipt and frappe.db.exists("Purchase Receipt", self.purchase_receipt):
			pr = frappe.get_doc("Purchase Receipt", self.purchase_receipt)
			if pr.docstatus == 1:
				pr.flags.ignore_permissions = True
				pr.cancel()
