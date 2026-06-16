from flask import Blueprint

from app.models.sample_event import SampleEvent
from app.utils.auth import role_required

operations_timeline_web_bp = Blueprint(
    "operations_timeline_web",
    __name__
)

@operations_timeline_web_bp.route("/operations/timeline")
@role_required("SUPER_ADMIN")
def operations_timeline():

    events = SampleEvent.query.order_by(
        SampleEvent.created_at.desc()
    ).limit(200).all()

    rows = ""

    for event in events:

        color = "#0d6efd"

        if "COLLECT" in (event.event_type or ""):
            color = "#198754"

        elif "TRANSIT" in (event.event_type or ""):
            color = "#f97316"

        elif "RECEIVED" in (event.event_type or ""):
            color = "#7c3aed"

        rows += f"""
        <div style="
            background:white;
            margin-bottom:12px;
            padding:15px;
            border-left:6px solid {color};
            border-radius:8px;
        ">
            <strong>{event.event_type}</strong><br>
            {event.note or ''}<br>
            <small>{event.created_at}</small>
        </div>
        """

    return f"""
    <html>
    <body style="
        font-family:Arial;
        background:#f1f5f9;
        padding:30px;
    ">

        <h1>DxCon Operations Timeline</h1>

        {rows}

        <br>
        <a href="/dashboard">
            Back Dashboard
        </a>

    </body>
    </html>
    """
