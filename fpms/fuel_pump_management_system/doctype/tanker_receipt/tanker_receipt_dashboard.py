from frappe import _


def get_data():
	return {
		"fieldname": "tanker_receipt",
		"internal_links": {
			"Purchase Order": "purchase_order",
			"Purchase Receipt": "purchase_receipt",
			"Purchase Invoice": "purchase_invoice",
			"Tank": ["items", "tank"],
			"Item": ["items", "item"],
			"Fuel Charge Type": ["charges", "component"],
		},
		"transactions": [
			{"label": _("Buying"), "items": ["Purchase Order", "Purchase Receipt", "Purchase Invoice"]},
			{"label": _("Stock"), "items": ["Tank", "Item"]},
			{"label": _("Levies"), "items": ["Fuel Charge Type"]},
		],
	}
