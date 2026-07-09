# Copyright (c) 2026, Kodlyft and contributors
# For license information, please see license.txt

"""Scheduled tasks for FPMS."""

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate


def notify_license_expiry():
	"""Refresh license statuses and notify FPMS Managers of licenses due to expire."""
	licenses = frappe.get_all(
		"License and Compliance Register",
		filters={"expiry_date": ["is", "set"]},
		fields=["name", "license_type", "license_number", "expiry_date", "reminder_days", "status"],
	)

	today = getdate(nowdate())
	due = []
	for lic in licenses:
		expiry = getdate(lic.expiry_date)
		reminder_from = getdate(add_days(expiry, -(lic.reminder_days or 30)))
		if expiry < today:
			new_status = "Expired"
		elif reminder_from <= today:
			new_status = "Expiring Soon"
		else:
			new_status = "Active"

		if new_status != lic.status:
			frappe.db.set_value("License and Compliance Register", lic.name, "status", new_status)

		if new_status in ("Expiring Soon", "Expired"):
			due.append({**lic, "status": new_status})

	if due:
		_notify_managers(due)


def _notify_managers(due):
	recipients = _manager_emails()
	if not recipients:
		return

	rows = "\n".join(
		f"- {d['license_type']} {d['license_number'] or ''} — {d['status']} (expires {d['expiry_date']})"
		for d in due
	)
	frappe.sendmail(
		recipients=recipients,
		subject=_("FPMS: {0} license(s) expiring or expired").format(len(due)),
		message=_("The following licenses need attention:\n\n{0}").format(rows),
	)


def _manager_emails():
	users = frappe.get_all(
		"Has Role",
		filters={"role": "FPMS Manager", "parenttype": "User"},
		pluck="parent",
	)
	return [
		email
		for email in (frappe.db.get_value("User", u, "email") for u in set(users))
		if email and email not in ("Administrator", "Guest")
	]
