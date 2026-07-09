# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class DipChartEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		dip_mm: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		volume_litres: DF.Float
	# end: auto-generated types

	pass
