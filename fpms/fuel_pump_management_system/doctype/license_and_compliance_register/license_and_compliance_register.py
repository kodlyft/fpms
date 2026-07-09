# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate


class LicenseandComplianceRegister(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		authority: DF.Data | None
		company: DF.Link | None
		expiry_date: DF.Date | None
		issue_date: DF.Date | None
		license_number: DF.Data | None
		license_type: DF.Literal["OGRA", "Explosives", "Weights & Measures", "Fire Safety", "HDIP", "Other"]
		naming_series: DF.Literal["FPMS-LIC-.YYYY.-"]
		reminder_days: DF.Int
		status: DF.Literal["Active", "Expiring Soon", "Expired"]
	# end: auto-generated types

	def validate(self):
		self.set_status()

	def set_status(self):
		if not self.expiry_date:
			self.status = "Active"
			return

		today = getdate(nowdate())
		expiry = getdate(self.expiry_date)
		reminder_from = getdate(add_days(expiry, -(self.reminder_days or 30)))

		if expiry < today:
			self.status = "Expired"
		elif reminder_from <= today:
			self.status = "Expiring Soon"
		else:
			self.status = "Active"
