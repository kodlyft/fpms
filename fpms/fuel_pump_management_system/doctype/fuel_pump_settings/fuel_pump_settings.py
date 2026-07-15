# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FuelPumpSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from fpms.fuel_pump_management_system.doctype.fuel_price_component.fuel_price_component import (
			FuelPriceComponent,
		)

		apply_fuel_levies_on_purchase: DF.Check
		auto_stock_reconcile: DF.Check
		dealer_commission_account: DF.Link | None
		default_company: DF.Link | None
		default_customer: DF.Link | None
		default_pos_profile: DF.Link | None
		default_price_list: DF.Link | None
		default_purchase_charges: DF.Table[FuelPriceComponent]
		default_tanker_supplier: DF.Link | None
		enable_vcf: DF.Check
		excess_account: DF.Link | None
		shortage_account: DF.Link | None
		variance_threshold_pct: DF.Percent
	# end: auto-generated types

	pass
