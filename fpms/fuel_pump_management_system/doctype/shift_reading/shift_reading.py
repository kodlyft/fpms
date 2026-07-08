# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShiftReading(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from fpms.fuel_pump_management_system.doctype.shift_detail.shift_detail import ShiftDetail
		from frappe.types import DF

		amended_from: DF.Link | None
		reading_details: DF.Table[ShiftDetail]
		shift_end_time: DF.Time | None
		shift_start_time: DF.Time | None
		shift_type: DF.Link | None
	# end: auto-generated types

	pass
