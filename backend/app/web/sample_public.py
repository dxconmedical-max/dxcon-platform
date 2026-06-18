from flask import Blueprint

from app.models.sample_tracking import SampleTracking
from app.models.sample_event import SampleEvent


sample_public_web_bp = Blueprint(
    "sample_public_web",
    __name__
)


def badge_color(status):
    return {
        "CHECKED_IN": "#198754",
        "IN_TRANSIT": "#f97316",
        "RECEIVED": "#7c3aed",
        "PROCESSING": "#0d6efd",
        "COMPLETED": "#198754",
        "COLLECTED": "#f97316",
    }.get(status or "", "#64748b")


@sample_public_web_bp.route("/samples/track/<sample_code>")
def track_sample(sample_code):

    sample = SampleTracking.query.filter_by(
        sample_code=sample_code
    ).first()

    if not sample:
        return """
        <html>
        <body style="font-family:Arial;padding:30px;background:#f1f5f9;">
            <div style="background:white;padding:25px;border-radius:12px;">
                <h1>Sample Not Found</h1>
                <p>The sample code is invalid or not available yet.</p>
            </div>
        </body>
        </html>
        """, 404

    events = SampleEvent.query.filter_by(
        sample_tracking_id=sample.id
    ).order_by(
        SampleEvent.created_at.asc()
    ).all()

    event_html = ""

    for e in events:
        event_html += f"""
        <div style="border-left:6px solid {badge_color(e.event_type)};background:#f8fafc;padding:14px;margin-bottom:12px;border-radius:8px;">
            <b>{e.event_type}</b><br>
            <span>{e.note or ""}</span><br>
            <small>{e.created_at}</small>
        </div>
        """

    map_link = ""

    if sample.map_url():
        map_link = f"""
        <p>
            <a href="{sample.map_url()}" target="_blank">
                Open GPS Map
            </a>
        </p>
        """

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>DxCon Sample Tracking</title>
    </head>
    <body style="font-family:Arial;background:#f1f5f9;margin:0;padding:20px;">

        <div style="background:#0a4b5c;color:white;padding:20px;border-radius:14px;margin-bottom:18px;">
            <h1>DxCon Sample Tracking</h1>
            <p>Sample chain-of-custody tracking</p>
        </div>

        <div style="background:white;padding:20px;border-radius:14px;margin-bottom:18px;">
            <h2>{sample.sample_code}</h2>

            <p>
                <b>Status:</b>
                <span style="background:{badge_color(sample.status)};color:white;padding:6px 10px;border-radius:8px;">
                    {sample.status}
                </span>
            </p>

            <p><b>Collector:</b> {sample.collector_id or ""}</p>
            <p><b>Transport Box:</b> {sample.transport_box_id or ""}</p>
            <p><b>Updated:</b> {sample.updated_at or ""}</p>

            {map_link}
        </div>

        <div style="background:white;padding:20px;border-radius:14px;">
            <h2>Timeline</h2>
            {event_html or "<p>No tracking event yet.</p>"}
        </div>

    </body>
    </html>
    """
