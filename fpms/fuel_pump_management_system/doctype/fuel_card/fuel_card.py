# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FuelCard(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		balance: DF.Currency
		card_number: DF.Data
		credit_limit: DF.Currency
		customer: DF.Link
		fleet: DF.Link | None
		status: DF.Literal["Active", "Blocked", "Expired"]
		valid_upto: DF.Date | None
	# end: auto-generated types

	pass
