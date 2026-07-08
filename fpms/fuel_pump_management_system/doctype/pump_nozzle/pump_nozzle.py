# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class PumpNozzle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		nozel_id: DF.Data | None
		nozel_name: DF.Data
	# end: auto-generated types

	def autoname(self):
		if self.nozel_id:
			self.name = self.nozel_id
		else:
			self.name = make_autoname("PN-.####")

	def validate(self):
		if not self.nozel_id:
			self.nozel_id = self.name
