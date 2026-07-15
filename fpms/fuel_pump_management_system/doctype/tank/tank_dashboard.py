from frappe import _


def get_data():
	return {
		"fieldname": "tank",
		"internal_links": {"Warehouse": "warehouse", "Item": "item"},
		"transactions": [
			{"label": _("Operations"), "items": ["Dip Reading", "Tanker Receipt", "Nozzle"]},
			{"label": _("Stock"), "items": ["Warehouse", "Item"]},
		],
	}
