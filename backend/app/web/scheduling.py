from flask import Blueprint, redirect, request

from app.models.booking_assignment import BookingAssignment
from app.models.driver import Driver
from app.models.marketplace_booking import MarketplaceBooking
from app.models.partner import Partner
from app.models.partner_capacity import PartnerCapacity
from app.services.booking_assignment import BookingAssignmentError, BookingAssignmentService
from app.services.scheduling import SchedulingError, SchedulingService
from app.services.slot_generation import SlotGenerationService


scheduling_web_bp = Blueprint(
    "scheduling_web",
    __name__,
)


def _page_styles():
    return """
    body { margin: 0; font-family: Arial, sans-serif; background: #f1f5f9; color: #0f172a; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: #0a4b5c; color: white; padding: 24px; }
    .sidebar h2 { margin-top: 0; margin-bottom: 30px; }
    .menu a { display: block; color: white; text-decoration: none; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,.15); }
    .content { flex: 1; padding: 32px; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; gap: 16px; flex-wrap: wrap; }
    .btn { background: #0d6efd; color: white; padding: 12px 18px; border-radius: 8px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; display: inline-block; }
    .btn-secondary { background: #6c757d; }
    .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    th { background: #e2e8f0; text-align: left; padding: 14px; }
    td { padding: 14px; border-bottom: 1px solid #e5e7eb; }
    .badge { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: bold; margin-right: 6px; }
    """


def _sidebar_html():
    return """
    <div class="sidebar">
        <h2>DxCon</h2>
        <div class="menu">
            <a href="/dashboard">Dashboard</a>
            <a href="/scheduling">Scheduling</a>
            <a href="/scheduling/collectors">Collectors</a>
            <a href="/marketplace">Marketplace</a>
            <a href="/partners">Partners</a>
        </div>
    </div>
    """


@scheduling_web_bp.route("/scheduling")
def scheduling_page():
    partners = Partner.query.order_by(Partner.display_name.asc()).limit(20).all()
    rows = ""
    for partner in partners:
        rows += f"""
        <tr>
            <td><a href="/scheduling/partners/{partner.id}">{partner.display_name}</a></td>
            <td>{partner.partner_type}</td>
            <td>{partner.city or ""}</td>
            <td>{partner.status}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Scheduling - DxCon</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Scheduling Engine</h1>
                    <a class="btn btn-secondary" href="/scheduling/collectors">Collector Availability</a>
                </div>
                <div class="card">
                    <p>Select a partner to view slots, capacity, and assignment actions.</p>
                </div>
                <table>
                    <tr><th>Partner</th><th>Type</th><th>City</th><th>Status</th></tr>
                    {rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@scheduling_web_bp.route("/scheduling/partners/<partner_id>")
def scheduling_partner_page(partner_id):
    try:
        partner = Partner.query.get(partner_id)
        if not partner:
            raise SchedulingError("Partner not found", 404)

        slot_date = request.args.get("date")
        slots = SchedulingService.list_available_slots(
            partner_id,
            slot_date=slot_date,
            include_full=True,
        )
        capacities = PartnerCapacity.query.filter_by(partner_id=partner_id).order_by(
            PartnerCapacity.date.asc()
        ).limit(14).all()
        bookings = MarketplaceBooking.query.filter_by(partner_id=partner_id).order_by(
            MarketplaceBooking.created_at.desc()
        ).limit(10).all()
        collectors = Driver.query.filter_by(status="ACTIVE").limit(10).all()
    except SchedulingError:
        return "<h1>Partner not found</h1>", 404

    slot_rows = ""
    for slot in slots:
        slot_rows += f"""
        <tr>
            <td>{slot.slot_date}</td>
            <td>{slot.start_time}-{slot.end_time}</td>
            <td>{slot.capacity}</td>
            <td>{slot.booked_count}</td>
            <td>{max(0, slot.capacity - slot.booked_count)}</td>
            <td>{slot.status}</td>
        </tr>
        """

    capacity_rows = ""
    for capacity in capacities:
        capacity_rows += f"""
        <tr>
            <td>{capacity.date}</td>
            <td>{capacity.service_type}</td>
            <td>{capacity.maximum_capacity}</td>
            <td>{capacity.booked_count}</td>
            <td>{capacity.remaining_capacity}</td>
        </tr>
        """

    booking_rows = ""
    for booking in bookings:
        assignment = BookingAssignment.query.filter_by(booking_id=booking.id).first()
        assign_form = ""
        if collectors:
            options = "".join(
                f'<option value="{collector.id}">{collector.full_name}</option>'
                for collector in collectors
            )
            assign_form = f"""
            <form method="POST" action="/scheduling/bookings/{booking.id}/assign-collector" style="display:inline;">
                <select name="collector_id">{options}</select>
                <button class="btn" type="submit">Assign</button>
            </form>
            """
        booking_rows += f"""
        <tr>
            <td>{booking.booking_code}</td>
            <td>{booking.requested_date or ""} {booking.requested_time_slot or ""}</td>
            <td>{booking.status}</td>
            <td>{assignment.assignment_status if assignment else "-"}</td>
            <td>{assign_form}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>{partner.display_name} Scheduling</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>{partner.display_name}</h1>
                    <div>
                        <a class="btn btn-secondary" href="/scheduling">Back</a>
                        <a class="btn" href="/scheduling/partners/{partner.id}/generate-slots">Generate 7-Day Slots</a>
                    </div>
                </div>
                <div class="card">
                    <form method="GET">
                        <label>Filter date</label>
                        <input name="date" value="{slot_date or ''}" placeholder="2026-06-26" />
                        <button class="btn" type="submit">Filter</button>
                    </form>
                </div>
                <h2>Slots</h2>
                <table>
                    <tr><th>Date</th><th>Time</th><th>Capacity</th><th>Booked</th><th>Remaining</th><th>Status</th></tr>
                    {slot_rows or "<tr><td colspan='6'>No slots yet. Generate slots to begin.</td></tr>"}
                </table>
                <h2>Partner Capacity</h2>
                <table>
                    <tr><th>Date</th><th>Service</th><th>Max</th><th>Booked</th><th>Remaining</th></tr>
                    {capacity_rows}
                </table>
                <h2>Recent Bookings</h2>
                <table>
                    <tr><th>Code</th><th>Requested</th><th>Status</th><th>Assignment</th><th>Action</th></tr>
                    {booking_rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@scheduling_web_bp.route("/scheduling/partners/<partner_id>/generate-slots")
def scheduling_partner_generate_slots_page(partner_id):
    try:
        SlotGenerationService.generate_partner_daily_slots(partner_id, days=7)
    except Exception:
        pass
    return redirect(f"/scheduling/partners/{partner_id}")


@scheduling_web_bp.route("/scheduling/collectors")
def scheduling_collectors_page():
    records = BookingAssignmentService.list_collector_availability(
        city=request.args.get("city"),
        date=request.args.get("date"),
    )
    collectors = Driver.query.filter_by(status="ACTIVE").all()
    collector_names = {item.id: item.full_name for item in collectors}

    rows = ""
    for record in records:
        rows += f"""
        <tr>
            <td>{collector_names.get(record.collector_id, record.collector_id)}</td>
            <td>{record.date}</td>
            <td>{record.start_time}-{record.end_time}</td>
            <td>{record.city or ""}</td>
            <td>{record.district or ""}</td>
            <td>{record.max_jobs}</td>
            <td>{record.assigned_jobs}</td>
            <td>{record.status}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Collector Availability</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Collector Availability</h1>
                    <a class="btn btn-secondary" href="/scheduling">Back to Scheduling</a>
                </div>
                <table>
                    <tr>
                        <th>Collector</th><th>Date</th><th>Window</th><th>City</th><th>District</th>
                        <th>Max Jobs</th><th>Assigned</th><th>Status</th>
                    </tr>
                    {rows or "<tr><td colspan='8'>No collector availability records yet.</td></tr>"}
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@scheduling_web_bp.route("/scheduling/bookings/<booking_id>/assign-collector", methods=["POST"])
def scheduling_assign_collector_page(booking_id):
    collector_id = request.form.get("collector_id")
    booking = MarketplaceBooking.query.get(booking_id)
    partner_id = booking.partner_id if booking else None

    try:
        BookingAssignmentService.assign_collector(booking_id, collector_id)
    except BookingAssignmentError:
        pass

    if partner_id:
        return redirect(f"/scheduling/partners/{partner_id}")
    return redirect("/scheduling")
