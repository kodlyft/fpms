# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.model.naming import make_autoname


class Nozzle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		current_totalizer: DF.Float
		dispenser: DF.Link | None
		item: DF.Link | None
		last_calibration: DF.Date | None
		next_calibration_due: DF.Date | None
		nozzle_id: DF.Data | None
		nozzle_name: DF.Data
		status: DF.Literal["Active", "Inactive", "Under Maintenance"]
		tank: DF.Link
	# end: auto-generated types

	def autoname(self):
		if self.nozzle_id:
			self.name = self.nozzle_id
		else:
			self.name = make_autoname("PN-.####")

	def validate(self):
		if not self.nozzle_id:
			self.nozzle_id = self.name
