import frappe


@frappe.whitelist()
def share_booking(booking_name, user_email):
    booking = frappe.get_doc("Booking", booking_name)

    if not frappe.has_permission(booking, "read"):
        frappe.throw("You do not have permission to share this booking")

    frappe.share.add(
        "Booking",
        booking_name,
        user_email,
        read=1,
        write=0,
        share=0,
        notify=1
    )

    return {
        "status": "success",
        "message": f"Booking {booking_name} shared with {user_email}"
    }
def booking_permission_query(user):
    if not user:
        user = frappe.session.user

    if "Hatch Member" in frappe.get_roles(user):
        return """`tabBooking`.`member` IN (
            SELECT `name`
            FROM `tabMember`
            WHERE `user` = {0}
        )""".format(frappe.db.escape(user))

    return ""

@frappe.whitelist()
def get_bookings_unsafe():
    return frappe.get_all(
        "Booking",
        fields=["*"]
    )

@frappe.whitelist()
def get_bookings_safe():
    bookings = frappe.get_list(
        "Booking",
        fields=[
            "name",
            "member",
            "resource",
            "booking_date",
            "start_time",
            "status"
           ]
    )

    # Hide sensitive info
    if "Front Desk Staff" not in frappe.get_roles():
        for booking in bookings:
            booking.pop("member_email", None)
            booking.pop("member_phone", None)

    return bookings

@frappe.whitelist()
def send_booking_confirmation_email(booking_name):
    booking = frappe.get_doc("Booking", booking_name)

    frappe.sendmail(
        recipients=[booking.member],
        subject=f"Booking {booking.name} Confirmed",
        message=f"Your booking {booking.name} has been confirmed."
    )
@frappe.whitelist()
def rename_member(old_name, new_name):
    return frappe.rename_doc(
        "Member",
        old_name,
        new_name,
        merge=False
    )
