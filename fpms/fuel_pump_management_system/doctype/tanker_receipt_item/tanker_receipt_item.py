# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class TankerReceiptItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		bol_litres: DF.Float
		density: DF.Float
		dip_after_mm: DF.Float
		dip_before_mm: DF.Float
		item: DF.Link | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		rate: DF.Currency
		received_litres: DF.Float
		shortfall_litres: DF.Float
		tank: DF.Link
		temperature: DF.Float
		volume_after: DF.Float
		volume_before: DF.Float
	# end: auto-generated types

	pass
