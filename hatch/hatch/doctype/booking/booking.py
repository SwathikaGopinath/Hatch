import frappe
from frappe.model.document import Document


class Booking(Document):
#time validation and amount computation
    def validate(self):
        self.validate_time()
        self.calculate_amounts()
        self.validate_capacity()

    def validate_time(self):
        if self.end_time <= self.start_time:
            frappe.throw("End Time must be greater than Start Time")

    def calculate_amounts(self):
        resource = frappe.get_doc("Resource", self.resource)

        start = frappe.utils.get_time(self.start_time)
        end = frappe.utils.get_time(self.end_time)

        duration = (
            (end.hour * 3600 + end.minute * 60 + end.second)
            - (start.hour * 3600 + start.minute * 60 + start.second)
        ) / 3600

        self.base_amount = resource.hourly_rate * duration

        self.addons_total = 0

        for row in self.addons:
            row.amount = row.rate * row.quantity
            self.addons_total += row.amount

        self.total_amount = self.base_amount + self.addons_total
#The capacity check — the actual forcing function
    def validate_capacity(self):
        resource = frappe.get_doc("Resource", self.resource)
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
            self.name,
            self.resource,
            self.booking_date,
            self.end_time,
            self.start_time,
        ),
    )

        existing_headcount = result[0][0] or 0
        available_seats = resource.capacity - existing_headcount

        if existing_headcount + self.headcount > resource.capacity:
            frappe.throw(
                f"Only {available_seats} seats are available for this time slot."
        )
    def before_submit(self):
        if self.status != "Pending Confirmation":
            frappe.throw(
                "Only bookings with status 'Pending Confirmation' can be submitted."
        )
    def on_submit(self):
        self.db_set("status", "Confirmed")
        frappe.enqueue(
            "hatch.api.send_booking_confirmation_email",
            booking_name=self.name
    )
    def on_cancel(self):
        self.db_set("status", "Cancelled")
    def on_trash(self):
        if self.status not in ("Draft", "Cancelled"):
            frappe.throw(
            "Only Draft or Cancelled bookings can be deleted."
        )
    def on_update(self):
        pass