from frappe import _


def get_data():
	return {
		"fieldname": "component",
		"internal_links": {"Account": "default_account"},
		"transactions": [
			{"label": _("Pricing"), "items": ["Fuel Price Notification"]},
			{"label": _("Buying"), "items": ["Tanker Receipt"]},
			{"label": _("Accounting"), "items": ["Account"]},
		],
	}
