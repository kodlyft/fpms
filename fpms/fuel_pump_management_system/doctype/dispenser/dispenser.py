# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class Dispenser(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		company: DF.Link | None
		dispenser_name: DF.Data
		last_calibration: DF.Date | None
		location: DF.Data | None
		next_calibration_due: DF.Date | None
		status: DF.Literal["Active", "Inactive", "Under Maintenance"]
		wm_seal_no: DF.Data | None
	# end: auto-generated types

	pass
