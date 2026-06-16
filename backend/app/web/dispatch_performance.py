from flask import Blueprint

from app.models.dispatch_job import DispatchJob
from app.utils.auth import role_required

dispatch_performance_web_bp = Blueprint(
    "dispatch_performance_web",
    __name__
)

@dispatch_performance_web_bp.route("/dispatch-performance")
@role_required("SUPER_ADMIN")
def dispatch_performance():

    jobs = DispatchJob.query.all()

    total_jobs = len(jobs)

    completed_jobs = len([
        j for j in jobs
        if j.status == "COMPLETED"
    ])

    avg_delay = 0

    if jobs:
        avg_delay = round(
            sum(j.delay_minutes or 0 for j in jobs)
            / len(jobs),
            1
        )

    avg_route_score = 0

    if jobs:
        avg_route_score = round(
            sum(j.route_score or 0 for j in jobs)
            / len(jobs),
            1
        )

    rows = ""

    for job in jobs:

        rows += f"""
        <tr>
            <td>{job.job_code}</td>
            <td>{job.priority}</td>
            <td>{job.status}</td>
            <td>{job.total_distance_km}</td>
            <td>{job.delay_minutes}</td>
            <td>{job.route_score}</td>
        </tr>
        """

    return f'''
    <html>
    <body style="font-family:Arial;padding:30px;background:#f1f5f9;">

        <h1>Dispatch Optimizer V2</h1>

        <h3>Total Jobs: {total_jobs}</h3>
        <h3>Completed Jobs: {completed_jobs}</h3>
        <h3>Average Delay: {avg_delay} min</h3>
        <h3>Average Route Score: {avg_route_score}</h3>

        <table border="1" cellpadding="10"
               style="width:100%;background:white;border-collapse:collapse;">
            <tr>
                <th>Job</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Distance</th>
                <th>Delay</th>
                <th>Route Score</th>
            </tr>
            {rows}
        </table>

    </body>
    </html>
    '''
