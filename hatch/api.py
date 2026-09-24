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
@frappe.whitelist()
def check_booking_availability(
    resource,
    booking_date,
    start_time,
    end_time,
    booking=None
):
    resource_doc = frappe.get_doc("Resource", resource)

    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(headcount), 0)
        FROM `tabBooking`
        WHERE name != %s
        AND resource = %s
        AND booking_date = %s
        AND status IN (
            'Pending Confirmation',
            'Confirmed',
            'Checked-In'
        )
        AND start_time < %s
        AND end_time > %s
        """,
        (
            booking or "",
            resource,
            booking_date,
            end_time,
            start_time,
        ),
    )

    existing_headcount = result[0][0] or 0
    available_seats = resource_doc.capacity - existing_headcount

    return {
        "available": max(available_seats, 0),
        "capacity": resource_doc.capacity,
        "message": f"{max(available_seats, 0)} of {resource_doc.capacity} seats free."
    }
@frappe.whitelist()
def reassign_booking_resource(booking, resource):
    booking_doc = frappe.get_doc("Booking", booking)

    if booking_doc.docstatus != 1:
        frappe.throw("Only submitted bookings can be reassigned.")

    if booking_doc.status != "Confirmed":
        frappe.throw("Only Confirmed bookings can be reassigned.")

    resource_doc = frappe.get_doc("Resource", resource)

    if booking_doc.headcount > resource_doc.capacity:
        frappe.throw(
            f"Cannot reassign this booking. "
            f"The selected resource has a capacity of {resource_doc.capacity}, "
            f"but this booking requires {booking_doc.headcount} seats."
        )

    booking_doc.db_set("resource", resource)

    return {
        "success": True,
        "resource": resource
    }
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_allowed_resources(doctype, txt, searchfield, start, page_len, filters):
    member = filters.get("member")

    if not member:
        return []

    membership_plan = frappe.db.get_value(
        "Member",
        member,
        "membership_plan"
    )

    if not membership_plan:
        return []

    allowed_resource_types = frappe.get_all(
        "Membership Plan Resource Type",
        filters={
            "parent": membership_plan,
            "parenttype": "Membership Plan"
        },
        pluck="resource_type"
    )

    if not allowed_resource_types:
        return []

    return frappe.db.sql(
        """
        SELECT name, resource_type
        FROM `tabResource`
        WHERE resource_type IN %(resource_types)s
        AND name LIKE %(txt)s
        ORDER BY name
        LIMIT %(start)s, %(page_len)s
        """,
        {
            "resource_types": tuple(allowed_resource_types),
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }
    )
def release_expired_holds():
    run_key = f"release_holds:{frappe.utils.now_datetime().strftime('%Y%m%d%H')}"

    if frappe.cache().get_value(run_key):
        return

    frappe.cache().set_value(
        run_key,
        True,
        expires_in_sec=3500
    )

    settings = frappe.get_single("Hatch Settings")

    expiry_hours = settings.pending_confirmation_expiry_hours

    if not expiry_hours:
        return

    expiry_time = frappe.utils.add_to_date(
        frappe.utils.now_datetime(),
        hours=-expiry_hours
    )

    bookings = frappe.get_all(
        "Booking",
        filters={
            "status": "Pending Confirmation",
            "creation": ["<", expiry_time]
        },
        pluck="name"
    )

    for booking_name in bookings:
        booking = frappe.get_doc("Booking", booking_name)

        booking.db_set("status", "Cancelled")

        frappe.db.set_value(
            "Booking",
            booking_name,
            "payment_status",
            "Unpaid"
        )
def get_booking_members_bulk():
    bookings = frappe.get_all(
        "Booking",
        fields=["name", "member"]
    )

    member_names = list({
        booking.member
        for booking in bookings
        if booking.member
    })

    members = frappe.get_all(
        "Member",
        filters={"name": ["in", member_names]},
        fields=["name", "member_name", "email"]
    )

    members_by_name = {
        member.name: member
        for member in members
    }

    for booking in bookings:
        member = members_by_name.get(booking.member)

        if member:
            print(member.member_name, member.email)
