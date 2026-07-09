# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FuelChargeType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		charge_type: DF.Data
		company: DF.Link
		default_account: DF.Link | None
		description: DF.SmallText | None
		disabled: DF.Check
	# end: auto-generated types

	pass
