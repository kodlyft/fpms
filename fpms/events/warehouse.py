import frappe


def on_load(doc, method):
    doc.actual_stock = (
        frappe.db.sql(
            """
        SELECT SUM(actual_qty) AS actual_stock
        FROM `tabBin`
        WHERE warehouse = %s
        """,
            (doc.name,),
            as_dict=True,
        )[0].actual_stock
        or 0
    )
    doc.available_capacity_litres = doc.warehouse_capacity - doc.actual_stock
