from flask import Blueprint

from app.models.home_collection import HomeCollection
from app.models.sample_tracking import SampleTracking

collector_console_web_bp = Blueprint(
    "collector_console_web",
    __name__
)


@collector_console_web_bp.route("/collector")
def collector_console():

    jobs_html = ""

    jobs = HomeCollection.query.all()

    for job in jobs:

        jobs_html += f"""
        <tr>
            <td>{job.id}</td>
            <td>{job.address}</td>
            <td>{job.scheduled_time}</td>
            <td>{job.status}</td>
            <td>
                <a href="/api/v1/collector/checkin/{job.id}">
                    Check In
                </a>
            </td>
            <td>
                <a href="/api/v1/collector/collected/{job.id}">
                    Collected
                </a>
            </td>
        </tr>
        """

    sample_html = ""

    samples = SampleTracking.query.all()

    for sample in samples:

        sample_html += f"""
        <tr>
            <td>{sample.sample_code}</td>
            <td>{sample.status}</td>
            <td>
                <a href="/api/v1/collector/received/{sample.id}">
                    Received
                </a>
            </td>
            <td>
                <a href="/api/v1/collector/processing/{sample.id}">
                    Processing
                </a>
            </td>
            <td>
                <a href="/api/v1/collector/completed/{sample.id}">
                    Completed
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;padding:30px;background:#f1f5f9">

        <h1>DxCon Collector Console</h1>

        <h2>Collection Jobs</h2>

        <table border="1" cellpadding="10" style="background:white;width:100%">
            <tr>
                <th>ID</th>
                <th>Address</th>
                <th>Schedule</th>
                <th>Status</th>
                <th>Check In</th>
                <th>Collected</th>
            </tr>

            {jobs_html}
        </table>

        <br><br>

        <h2>Samples</h2>

        <table border="1" cellpadding="10" style="background:white;width:100%">
            <tr>
                <th>Sample Code</th>
                <th>Status</th>
                <th>Received</th>
                <th>Processing</th>
                <th>Completed</th>
            </tr>

            {sample_html}
        </table>

    </body>
    </html>
    """
