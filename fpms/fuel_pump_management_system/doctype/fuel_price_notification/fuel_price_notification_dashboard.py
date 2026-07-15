from frappe import _


def get_data():
	return {
		"fieldname": "item",
		"internal_links": {
			"Item Price": "item_price",
			"Item": "item",
			"Price List": "price_list",
			"Fuel Charge Type": ["components", "component"],
		},
		"transactions": [
			{"label": _("Pricing"), "items": ["Item Price", "Price List"]},
			{"label": _("Build-up"), "items": ["Item", "Fuel Charge Type"]},
		],
	}
