import frappe


def after_install():
  
    default_resources = [
        "Room A",
        "Room B",
        "Hot Desk Zone",
        "Meeting Room",
    ]

    for resource_name in default_resources:
        if not frappe.db.exists("Resource", {"resource_name": resource_name}):
            frappe.get_doc({
                "doctype": "Resource",
                "resource_name": resource_name,
                "capacity": 10,
                "hourly_rate": 500
            }).insert(ignore_permissions=True)

    if not frappe.db.exists("Hatch Settings"):
        frappe.get_doc({
            "doctype": "Hatch Settings",
            "manager_email": "manager@test.com",
            "pending_confirmation_expiry_hours": 24,
            "cancellation_window_hours": 2,
            "waitlist_enabled": 1
        }).insert(ignore_permissions=True)

    frappe.msgprint("Hatch installation completed successfully.")
