# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from fpms.events.purchase_taxes import ALLOWED_ACCOUNT_TYPES


class FuelChargeType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		category: DF.Literal["Valuation and Total", "Total", "Valuation"]
		charge_type: DF.Data
		company: DF.Link
		default_account: DF.Link | None
		description: DF.SmallText | None
		disabled: DF.Check
		included_in_rate: DF.Check
	# end: auto-generated types

	def validate(self):
		self.validate_account()
		self.validate_category()

	def validate_account(self):
		if not self.default_account:
			return

		account_type, company, is_group = frappe.get_cached_value(
			"Account", self.default_account, ["account_type", "company", "is_group"]
		)
		if is_group:
			frappe.throw(_("Levy Account cannot be a group account."))
		if company != self.company:
			frappe.throw(_("Levy Account must belong to {0}.").format(frappe.bold(self.company)))
		if account_type not in ALLOWED_ACCOUNT_TYPES:
			frappe.throw(
				_("Levy Account must be of type {0}, not {1}.").format(
					", ".join(ALLOWED_ACCOUNT_TYPES), frappe.bold(account_type or _("None"))
				)
			)

	def validate_category(self):
		"""ERPNext refuses to carve a pure-valuation charge out of the item rate."""
		if self.included_in_rate and self.category == "Valuation":
			frappe.throw(_('A charge included in the supplier rate cannot use the "Valuation" category.'))
