# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class FuelPriceNotification(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from fpms.fuel_pump_management_system.doctype.fuel_price_component.fuel_price_component import (
			FuelPriceComponent,
		)

		amended_from: DF.Link | None
		components: DF.Table[FuelPriceComponent]
		effective_from: DF.Datetime
		ex_depot_price: DF.Currency
		item: DF.Link
		item_price: DF.Link | None
		naming_series: DF.Literal["FPMS-PRICE-.YYYY.-"]
		ogra_reference: DF.Data | None
		price_list: DF.Link
		retail_price: DF.Currency
		status: DF.Literal["Draft", "Submitted", "Cancelled"]
	# end: auto-generated types

	def validate(self):
		self.set_retail_price()
		self.set_status()

	def on_submit(self):
		self.create_item_price()
		self.db_set("status", self._status_value())

	def on_cancel(self):
		self.remove_item_price()
		self.db_set("status", self._status_value())

	def set_retail_price(self):
		self.retail_price = flt(self.ex_depot_price) + sum(flt(c.rate_per_litre) for c in self.components)

	def set_status(self):
		self.status = self._status_value()

	def _status_value(self):
		return {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus]

	def create_item_price(self):
		"""Publish the notified retail price as a dated, effective ERPNext Item Price.

		Validity is enforced purely through the ``valid_from`` date on the Item Price. Never
		through Pricing Rule ``valid_upto`` (frappe/erpnext#50122).
		"""
		if self.item_price:
			return

		valid_from = getdate(self.effective_from)
		existing = frappe.db.get_value(
			"Item Price",
			{
				"item_code": self.item,
				"price_list": self.price_list,
				"selling": 1,
				"valid_from": valid_from,
			},
		)
		if existing:
			ip = frappe.get_doc("Item Price", existing)
			ip.price_list_rate = self.retail_price
			ip.flags.ignore_permissions = True
			ip.save()
		else:
			ip = frappe.new_doc("Item Price")
			ip.item_code = self.item
			ip.price_list = self.price_list
			ip.selling = 1
			ip.price_list_rate = self.retail_price
			ip.valid_from = valid_from
			ip.flags.ignore_permissions = True
			ip.insert()

		self.db_set("item_price", ip.name)

	def remove_item_price(self):
		item_price = self.item_price
		if not item_price:
			return

		self.db_set("item_price", None)

		if frappe.db.exists("Item Price", item_price):
			try:
				frappe.delete_doc("Item Price", item_price, ignore_permissions=True, force=True)
			except frappe.LinkExistsError:
				frappe.msgprint(
					_("Item Price {0} is used elsewhere and was kept.").format(item_price),
					alert=True,
				)
