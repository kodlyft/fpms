from frappe import _


def get_data():
	return {
		"fieldname": "nozzle",
		"internal_links": {
			"Dispenser": "dispenser",
			"Tank": "tank",
			"Item": "item",
		},
		"transactions": [
			{"label": _("Shifts"), "items": ["Shift Reconciliation"]},
			{"label": _("Equipment"), "items": ["Dispenser", "Tank", "Item"]},
		],
	}
