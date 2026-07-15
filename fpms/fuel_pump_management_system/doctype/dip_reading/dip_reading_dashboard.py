from frappe import _


def get_data():
	return {
		"fieldname": "tank",
		"internal_links": {
			"Tank": "tank",
			"Item": "item",
			"Employee": "employee",
			"Stock Reconciliation": "stock_reconciliation",
		},
		"transactions": [
			{"label": _("Wet Stock"), "items": ["Tank", "Item"]},
			{"label": _("Postings"), "items": ["Stock Reconciliation"]},
			{"label": _("Operator"), "items": ["Employee"]},
		],
	}
