from frappe import _


def get_data():
	return {
		"fieldname": "fleet",
		"internal_links": {"Customer": "customer", "Fuel Card": "fuel_card"},
		"transactions": [
			{"label": _("Credit"), "items": ["Customer", "Fuel Card"]},
		],
	}
