from frappe import _


def get_data():
	return {
		"fieldname": "fuel_card",
		"internal_links": {"Customer": "customer", "Fleet": "fleet"},
		"transactions": [
			{"label": _("Credit"), "items": ["Customer", "Fleet"]},
		],
	}
