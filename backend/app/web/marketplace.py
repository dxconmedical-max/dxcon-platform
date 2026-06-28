from flask import Blueprint, redirect, request

from app.services.marketplace_booking import MarketplaceBookingError, MarketplaceBookingService
from app.services.marketplace_search import MarketplaceSearchService


marketplace_web_bp = Blueprint(
    "marketplace_web",
    __name__,
)


def _page_styles():
    return """
    body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: #f1f5f9;
        color: #0f172a;
    }
    .layout { display: flex; min-height: 100vh; }
    .sidebar {
        width: 240px;
        background: #0a4b5c;
        color: white;
        padding: 24px;
    }
    .sidebar h2 { margin-top: 0; margin-bottom: 30px; }
    .menu a {
        display: block;
        color: white;
        text-decoration: none;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255,255,255,.15);
    }
    .content { flex: 1; padding: 32px; }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        gap: 16px;
        flex-wrap: wrap;
    }
    .btn {
        background: #0d6efd;
        color: white;
        padding: 12px 18px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        border: none;
        cursor: pointer;
        display: inline-block;
    }
    .btn-secondary { background: #6c757d; }
    .card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,.08);
        margin-bottom: 24px;
    }
    .filters {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
    }
    .field label { display: block; font-weight: bold; margin-bottom: 6px; font-size: 13px; }
    .field input, .field select {
        width: 100%;
        padding: 10px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        box-sizing: border-box;
    }
    .results {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
    }
    .result-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,.08);
        border: 1px solid #e2e8f0;
    }
    .result-card h3 { margin-top: 0; margin-bottom: 8px; }
    .meta { color: #64748b; font-size: 14px; margin: 6px 0; }
    .badge {
        display: inline-block;
        background: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 6px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,.08);
    }
    th { background: #e2e8f0; text-align: left; padding: 14px; }
    td { padding: 14px; border-bottom: 1px solid #e5e7eb; }
    """


def _sidebar_html():
    return """
    <div class="sidebar">
        <h2>DxCon</h2>
        <div class="menu">
            <a href="/dashboard">Dashboard</a>
            <a href="/marketplace">Marketplace</a>
            <a href="/marketplace/bookings">Bookings</a>
            <a href="/partners">Partners</a>
            <a href="/orders">Orders</a>
        </div>
    </div>
    """


@marketplace_web_bp.route("/marketplace", methods=["GET", "POST"])
def marketplace_page():
    params = {
        "q": request.values.get("q", ""),
        "province": request.values.get("province", ""),
        "city": request.values.get("city", ""),
        "district": request.values.get("district", ""),
        "partner_type": request.values.get("partner_type", ""),
        "home_collection": request.values.get("home_collection", ""),
        "max_price": request.values.get("max_price", ""),
        "sort": request.values.get("sort", "relevance"),
    }

    search = MarketplaceSearchService.search(
        q=params["q"] or None,
        province=params["province"] or None,
        city=params["city"] or None,
        district=params["district"] or None,
        partner_type=params["partner_type"] or None,
        home_collection=params["home_collection"] or None,
        max_price=params["max_price"] or None,
        sort=params["sort"] or "relevance",
    )

    cards = ""
    for item in search["results"]:
        partner = item["partner"]
        service = item["service"]
        price = f"{int(item['price']):,} {item['currency']}"
        eta = item["turnaround_hours"] or "-"
        tags = item.get("recommendation_tags") or []
        tag_badges = "".join(f'<span class="badge">{tag}</span>' for tag in tags)
        availability = item.get("availability") or {}
        next_slot = availability.get("next_available_time") or "-"
        cards += f"""
        <div class="result-card">
            <h3>{service['name']}</h3>
            <div class="meta">{partner['display_name']} · {partner['partner_type']}</div>
            <div class="meta">{partner.get('city') or ''} {partner.get('district') or ''}</div>
            <div style="margin: 12px 0;">
                <span class="badge">Trust {item['trust_score']}</span>
                <span class="badge">Rating {item['rating']:.1f}</span>
                <span class="badge">{price}</span>
            </div>
            <div class="meta">ETA: {eta} hours</div>
            <div class="meta">Next slot: {next_slot}</div>
            <div class="meta">Completed orders: {item['completed_orders']}</div>
            <div style="margin: 8px 0;">{tag_badges}</div>
            <div style="margin-top: 16px;">
                <a class="btn" href="/marketplace/book?mapping_id={item['mapping_id']}">Book Now</a>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>DxCon Marketplace</title>
        <style>{_page_styles()}</style>
    </head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Diagnostic Marketplace</h1>
                    <a class="btn btn-secondary" href="/marketplace/bookings">View Bookings</a>
                </div>
                <div class="card">
                    <form method="GET" class="filters">
                        <div class="field">
                            <label>Search</label>
                            <input name="q" value="{params['q']}" placeholder="HbA1c, CBC, lipid..." />
                        </div>
                        <div class="field">
                            <label>Province</label>
                            <input name="province" value="{params['province']}" placeholder="Ha Noi" />
                        </div>
                        <div class="field">
                            <label>City</label>
                            <input name="city" value="{params['city']}" />
                        </div>
                        <div class="field">
                            <label>District</label>
                            <input name="district" value="{params['district']}" />
                        </div>
                        <div class="field">
                            <label>Partner Type</label>
                            <select name="partner_type">
                                <option value="">Any</option>
                                <option value="LABORATORY" {"selected" if params['partner_type']=='LABORATORY' else ""}>LABORATORY</option>
                                <option value="CLINIC" {"selected" if params['partner_type']=='CLINIC' else ""}>CLINIC</option>
                                <option value="HOSPITAL" {"selected" if params['partner_type']=='HOSPITAL' else ""}>HOSPITAL</option>
                            </select>
                        </div>
                        <div class="field">
                            <label>Home Collection</label>
                            <select name="home_collection">
                                <option value="">Any</option>
                                <option value="true" {"selected" if params['home_collection']=='true' else ""}>Yes</option>
                                <option value="false" {"selected" if params['home_collection']=='false' else ""}>No</option>
                            </select>
                        </div>
                        <div class="field">
                            <label>Max Price</label>
                            <input name="max_price" value="{params['max_price']}" />
                        </div>
                        <div class="field">
                            <label>Sort</label>
                            <select name="sort">
                                <option value="relevance" {"selected" if params['sort']=='relevance' else ""}>Relevance</option>
                                <option value="price_asc" {"selected" if params['sort']=='price_asc' else ""}>Price Low-High</option>
                                <option value="price_desc" {"selected" if params['sort']=='price_desc' else ""}>Price High-Low</option>
                                <option value="rating_desc" {"selected" if params['sort']=='rating_desc' else ""}>Rating</option>
                                <option value="turnaround_asc" {"selected" if params['sort']=='turnaround_asc' else ""}>Fastest ETA</option>
                            </select>
                        </div>
                        <div class="field" style="display:flex;align-items:end;">
                            <button class="btn" type="submit">Search</button>
                        </div>
                    </form>
                </div>
                <p><strong>{search['count']}</strong> results found</p>
                <div class="results">{cards or "<p>No services found. Try seeding demo data.</p>"}</div>
            </div>
        </div>
    </body>
    </html>
    """


@marketplace_web_bp.route("/marketplace/book", methods=["GET"])
def marketplace_book_page():
    mapping_id = request.args.get("mapping_id", "")

    return f"""
    <html>
    <head><title>Book Service - DxCon</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Book Diagnostic Service</h1>
                    <a class="btn btn-secondary" href="/marketplace">Back to Search</a>
                </div>
                <div class="card">
                    <form method="POST" action="/marketplace/book">
                        <input type="hidden" name="mapping_id" value="{mapping_id}" />
                        <div class="field"><label>Patient Name</label><input name="patient_name" required /></div>
                        <div class="field"><label>Phone</label><input name="patient_phone" required /></div>
                        <div class="field"><label>Email</label><input name="patient_email" type="email" /></div>
                        <div class="field"><label>Address</label><input name="patient_address" /></div>
                        <div class="field"><label>Province</label><input name="province" /></div>
                        <div class="field"><label>City</label><input name="city" /></div>
                        <div class="field"><label>District</label><input name="district" /></div>
                        <div class="field"><label>Requested Date</label><input name="requested_date" placeholder="2026-06-26" /></div>
                        <div class="field"><label>Time Slot</label><input name="requested_time_slot" placeholder="08:00-10:00" /></div>
                        <div class="field"><label>Note</label><input name="note" /></div>
                        <button class="btn" type="submit">Create Booking</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@marketplace_web_bp.route("/marketplace/book", methods=["POST"])
def marketplace_book_submit_page():
    data = {
        "partner_service_mapping_id": request.form.get("mapping_id"),
        "patient_name": request.form.get("patient_name"),
        "patient_phone": request.form.get("patient_phone"),
        "patient_email": request.form.get("patient_email"),
        "patient_address": request.form.get("patient_address"),
        "province": request.form.get("province"),
        "city": request.form.get("city"),
        "district": request.form.get("district"),
        "requested_date": request.form.get("requested_date"),
        "requested_time_slot": request.form.get("requested_time_slot"),
        "note": request.form.get("note"),
    }

    try:
        booking = MarketplaceBookingService.create_booking(data)
        return redirect(f"/marketplace/bookings/{booking.id}")
    except MarketplaceBookingError:
        return redirect(f"/marketplace/book?mapping_id={request.form.get('mapping_id', '')}")


@marketplace_web_bp.route("/marketplace/bookings")
def marketplace_bookings_page():
    bookings = MarketplaceBookingService.list_bookings()

    rows = ""
    for booking in bookings:
        rows += f"""
        <tr>
            <td><a href="/marketplace/bookings/{booking.id}">{booking.booking_code}</a></td>
            <td>{booking.patient_name}</td>
            <td>{booking.patient_phone}</td>
            <td>{booking.status}</td>
            <td>{booking.requested_date or ""}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Marketplace Bookings</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Marketplace Bookings</h1>
                    <a class="btn btn-secondary" href="/marketplace">Back to Marketplace</a>
                </div>
                <table>
                    <tr>
                        <th>Code</th>
                        <th>Patient</th>
                        <th>Phone</th>
                        <th>Status</th>
                        <th>Requested Date</th>
                    </tr>
                    {rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@marketplace_web_bp.route("/marketplace/bookings/<booking_id>")
def marketplace_booking_detail_page(booking_id):
    try:
        booking = MarketplaceBookingService.get_booking_detail(booking_id)
    except MarketplaceBookingError:
        return "<h1>Booking not found</h1>", 404

    partner = booking.get("partner") or {}
    service = booking.get("service") or {}
    mapping = booking.get("mapping") or {}
    timeline_rows = ""
    for event in booking.get("timeline") or []:
        timeline_rows += f"""
        <tr>
            <td>{event['event_type']}</td>
            <td>{event.get('message') or ''}</td>
            <td>{event.get('actor_email') or ''}</td>
            <td>{event.get('created_at') or ''}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>{booking['booking_code']} - Booking</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Booking {booking['booking_code']}</h1>
                    <a class="btn btn-secondary" href="/marketplace/bookings">Back to Bookings</a>
                </div>
                <div class="card">
                    <p><strong>Status:</strong> {booking['status']}</p>
                    <p><strong>Patient:</strong> {booking['patient_name']} · {booking['patient_phone']}</p>
                    <p><strong>Email:</strong> {booking.get('patient_email') or ''}</p>
                    <p><strong>Address:</strong> {booking.get('patient_address') or ''}</p>
                    <p><strong>Location:</strong> {booking.get('province') or ''} / {booking.get('city') or ''} / {booking.get('district') or ''}</p>
                    <p><strong>Requested:</strong> {booking.get('requested_date') or ''} {booking.get('requested_time_slot') or ''}</p>
                    <p><strong>Partner:</strong> {partner.get('display_name') or ''}</p>
                    <p><strong>Service:</strong> {service.get('name') or ''}</p>
                    <p><strong>Price:</strong> {int(mapping.get('price') or 0):,} {mapping.get('currency') or 'VND'}</p>
                    <p><strong>ETA:</strong> {mapping.get('turnaround_hours') or '-'} hours</p>
                    <p><strong>Note:</strong> {booking.get('note') or ''}</p>
                </div>
                <h2>Timeline</h2>
                <table>
                    <tr>
                        <th>Event</th>
                        <th>Message</th>
                        <th>Actor</th>
                        <th>Time</th>
                    </tr>
                    {timeline_rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """
