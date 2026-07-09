# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FuelCreditSale(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		customer: DF.Link
		fleet: DF.Link | None
		fuel_card: DF.Link | None
		item: DF.Link
		litres: DF.Float
		nozzle: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		rate: DF.Currency
		sales_invoice: DF.Link | None
		vehicle_number: DF.Data | None
	# end: auto-generated types

	pass
