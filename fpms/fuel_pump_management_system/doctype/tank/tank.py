# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

from itertools import pairwise

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Tank(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from fpms.fuel_pump_management_system.doctype.dip_chart_entry.dip_chart_entry import DipChartEntry

		capacity_litres: DF.Float
		dip_chart: DF.Table[DipChartEntry]
		item: DF.Link
		status: DF.Literal["Active", "Inactive", "Under Maintenance"]
		tank_name: DF.Data
		warehouse: DF.Link
	# end: auto-generated types

	def validate(self):
		self.validate_dip_chart()

	def validate_dip_chart(self):
		"""Ensure the strapping chart is sorted by ascending dip with no duplicate depths."""
		last_dip = None
		for row in sorted(self.dip_chart, key=lambda r: flt(r.dip_mm)):
			if last_dip is not None and flt(row.dip_mm) == last_dip:
				frappe.throw(_("Duplicate dip depth {0} mm in the dip chart.").format(row.dip_mm))
			last_dip = flt(row.dip_mm)

	def interpolate_volume(self, dip_mm: float) -> float:
		"""
		Linearly interpolate the volume (litres) for a given dip depth (mm).

		Below the lowest charted dip returns 0; above the highest returns the max charted
		volume. Between points, interpolates linearly.
		"""
		chart = sorted(
			((flt(r.dip_mm), flt(r.volume_litres)) for r in self.dip_chart),
			key=lambda p: p[0],
		)
		if not chart:
			frappe.throw(_("Tank {0} has no dip chart configured.").format(self.name))

		dip_mm = flt(dip_mm)
		if dip_mm <= chart[0][0]:
			return chart[0][1] if dip_mm == chart[0][0] else 0.0
		if dip_mm >= chart[-1][0]:
			return chart[-1][1]

		for (d0, v0), (d1, v1) in pairwise(chart):
			if d0 <= dip_mm <= d1:
				if d1 == d0:
					return v1
				ratio = (dip_mm - d0) / (d1 - d0)
				return v0 + ratio * (v1 - v0)
		return chart[-1][1]
