# Hatch

A custom Frappe app for managing shared-desk resources, members, membership plans, and bookings.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH

bench get-app hatch https://github.com/SwathikaGopinath/Hatch --branch version-16

bench --site custom.local install-app hatch

bench --site custom.local migrate
```

## Features

* Resource management
* Membership Plans
* Member management
* Booking management
* Booking add-ons
* Booking capacity validation
* Booking lifecycle management
* Roles and permissions
* Record-level access control
* Query Builder
* Document lifecycle hooks
* Client-side availability filtering
* Scheduled jobs

## Main DocTypes

* Resource
* Membership Plan
* Member
* Booking
* Booking Add-on Entry
* Hatch Settings

## Architecture Decisions

* Built as a pure Frappe application.
* Server-side validation is used for business rules.
* Frappe Query Builder is used for database queries.
* Client Scripts handle UI-related behavior.
* Frappe permissions and row-level conditions control data access.
* Scheduled jobs handle background booking tasks.

## Booking Lifecycle

```text
Draft → Pending Confirmation → Confirmed → Checked-In → Completed
```

Bookings can also be cancelled according to the configured rules.

## Capacity Check

Hatch prevents overbooking by checking the total headcount of overlapping active bookings for the same resource.

```text
existing.start_time < current.end_time
AND
existing.end_time > current.start_time
```

## Scheduled Jobs

An hourly scheduled job releases expired booking holds based on the configured expiry time.

A cache sentinel prevents the same hourly run from being processed more than once.

## Known Issues

Some capstone requirements are not yet implemented.

Reports, print format, API/webhook, security hardening, and automated tests are pending.

## Run Tests

```bash
bench --site custom.local run-tests --app hatch
```

## Documentation

* `README.md` — Project overview, setup, architecture, and known issues.
* `README_internals.md` — Task-specific technical explanations and written answers.
