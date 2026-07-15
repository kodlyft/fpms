from frappe import _


def get_data():
	return {
		"fieldname": "fpms_shift",
		"non_standard_fieldnames": {
			"Sales Invoice": "fpms_shift",
			"POS Invoice": "fpms_shift",
		},
		"internal_links": {
			"Stock Entry": "stock_entry",
			"Employee": "employee",
			"Nozzle": ["reading_details", "nozzle"],
			"Customer": ["credit_sales", "customer"],
			"Mode of Payment": ["payment_details", "mode_of_payment"],
		},
		"transactions": [
			{"label": _("Selling"), "items": ["Sales Invoice", "POS Invoice"]},
			{"label": _("Stock"), "items": ["Stock Entry"]},
			{"label": _("Shift"), "items": ["Nozzle", "Employee"]},
			{"label": _("Credit"), "items": ["Customer"]},
			{"label": _("Collection"), "items": ["Mode of Payment"]},
		],
	}
