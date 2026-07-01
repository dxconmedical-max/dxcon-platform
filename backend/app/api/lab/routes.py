from flask import Blueprint, request

from app.services.accession_service import AccessionService, WorklistService
from app.services.analyzer_service import AnalyzerService
from app.services.delta_check_service import CriticalResultService, DeltaCheckService
from app.services.lab_dashboard_service import LabDashboardService
from app.services.lab_workflow_service import LabWorkflowError
from app.services.qc_service import QCService
from app.services.release_service import ReleaseService
from app.services.review_service import ReviewService


lab_bp = Blueprint("lab_operations", __name__, url_prefix="/api/v1/lab")


def _page_args():
    return request.args.get("page", 1), request.args.get("per_page", 20)


def _error(exc):
    return {"error": exc.message}, exc.status_code


def _actor():
    return request.headers.get("X-User-Email", "SYSTEM")


@lab_bp.route("/dashboard", methods=["GET"])
def lab_dashboard():
    return LabDashboardService.get_dashboard()


@lab_bp.route("/accessions", methods=["GET"])
def list_accessions():
    page, per_page = _page_args()
    return AccessionService.list_accessions(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        workflow_stage=request.args.get("workflow_stage"),
        worklist_id=request.args.get("worklist_id"),
        analyzer_id=request.args.get("analyzer_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/accessions", methods=["POST"])
def create_accession():
    data = request.get_json(silent=True) or {}
    if not data.get("sample_code"):
        return {"error": "sample_code is required"}, 400
    data["actor"] = _actor()
    accession = AccessionService.create_accession(data)
    return {"message": "Accession created", "accession": accession.to_dict()}, 201


@lab_bp.route("/accessions/<accession_id>", methods=["GET"])
def get_accession(accession_id):
    try:
        return {"accession": AccessionService.get_accession(accession_id)}
    except LabWorkflowError as exc:
        return _error(exc)


@lab_bp.route("/accessions/<accession_id>", methods=["PUT"])
def update_accession(accession_id):
    data = request.get_json(silent=True) or {}
    try:
        accession = AccessionService.update_accession(accession_id, data)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Accession updated", "accession": accession.to_dict()}


@lab_bp.route("/accessions/<accession_id>", methods=["DELETE"])
def delete_accession(accession_id):
    try:
        AccessionService.delete_accession(accession_id)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Accession deleted"}


@lab_bp.route("/accessions/<accession_id>/advance", methods=["POST"])
def advance_accession(accession_id):
    data = request.get_json(silent=True) or {}
    try:
        accession, transition = AccessionService.advance_accession(
            accession_id,
            actor=_actor(),
            target_stage=data.get("target_stage"),
        )
    except LabWorkflowError as exc:
        return _error(exc)
    return {
        "message": "Accession advanced",
        "accession": accession.to_dict(),
        "transition": transition.to_dict(),
    }


@lab_bp.route("/accessions/<accession_id>/receive", methods=["POST"])
def receive_accession(accession_id):
    try:
        accession, transition = AccessionService.receive_at_lab(accession_id, actor=_actor())
    except LabWorkflowError as exc:
        return _error(exc)
    return {
        "message": "Sample received at lab",
        "accession": accession.to_dict(),
        "transition": transition.to_dict(),
    }


@lab_bp.route("/worklists", methods=["GET"])
def list_worklists():
    page, per_page = _page_args()
    return WorklistService.list_worklists(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        lab_bench_id=request.args.get("lab_bench_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/worklists", methods=["POST"])
def create_worklist():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return {"error": "name is required"}, 400
    worklist = WorklistService.create_worklist(data)
    return {"message": "Worklist created", "worklist": worklist.to_dict()}, 201


@lab_bp.route("/worklists/<worklist_id>", methods=["GET"])
def get_worklist(worklist_id):
    try:
        return {"worklist": WorklistService.get_worklist(worklist_id)}
    except LabWorkflowError as exc:
        return _error(exc)


@lab_bp.route("/worklists/<worklist_id>", methods=["PUT"])
def update_worklist(worklist_id):
    data = request.get_json(silent=True) or {}
    try:
        worklist = WorklistService.update_worklist(worklist_id, data)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Worklist updated", "worklist": worklist.to_dict()}


@lab_bp.route("/worklists/<worklist_id>", methods=["DELETE"])
def delete_worklist(worklist_id):
    try:
        WorklistService.delete_worklist(worklist_id)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Worklist deleted"}


@lab_bp.route("/analyzers", methods=["GET"])
def list_analyzers():
    page, per_page = _page_args()
    return AnalyzerService.list_analyzers(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        lab_bench_id=request.args.get("lab_bench_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/analyzers", methods=["POST"])
def create_analyzer():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return {"error": "name is required"}, 400
    analyzer = AnalyzerService.create_analyzer(data)
    return {"message": "Analyzer created", "analyzer": analyzer.to_dict()}, 201


@lab_bp.route("/analyzers/<analyzer_id>", methods=["GET"])
def get_analyzer(analyzer_id):
    try:
        return {"analyzer": AnalyzerService.get_analyzer(analyzer_id)}
    except LabWorkflowError as exc:
        return _error(exc)


@lab_bp.route("/analyzers/<analyzer_id>", methods=["PUT"])
def update_analyzer(analyzer_id):
    data = request.get_json(silent=True) or {}
    try:
        analyzer = AnalyzerService.update_analyzer(analyzer_id, data)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Analyzer updated", "analyzer": analyzer.to_dict()}


@lab_bp.route("/analyzers/<analyzer_id>", methods=["DELETE"])
def delete_analyzer(analyzer_id):
    try:
        AnalyzerService.delete_analyzer(analyzer_id)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Analyzer deleted"}


@lab_bp.route("/queues", methods=["GET"])
def list_queues():
    page, per_page = _page_args()
    return AnalyzerService.list_queues(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        analyzer_id=request.args.get("analyzer_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/queues", methods=["POST"])
def enqueue_sample():
    data = request.get_json(silent=True) or {}
    if not data.get("analyzer_id") or not data.get("accession_id"):
        return {"error": "analyzer_id and accession_id are required"}, 400
    queue = AnalyzerService.enqueue_sample(
        data["analyzer_id"],
        data["accession_id"],
        actor=_actor(),
    )
    return {"message": "Sample queued", "queue": queue.to_dict()}, 201


@lab_bp.route("/queues/<queue_id>", methods=["GET"])
def get_queue(queue_id):
    try:
        return {"queue": AnalyzerService.get_queue(queue_id)}
    except LabWorkflowError as exc:
        return _error(exc)


@lab_bp.route("/queues/<queue_id>", methods=["PUT"])
def update_queue(queue_id):
    data = request.get_json(silent=True) or {}
    try:
        queue = AnalyzerService.update_queue(queue_id, data)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Queue updated", "queue": queue.to_dict()}


@lab_bp.route("/queues/<queue_id>", methods=["DELETE"])
def delete_queue(queue_id):
    try:
        AnalyzerService.delete_queue(queue_id)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Queue deleted"}


@lab_bp.route("/queues/<queue_id>/start", methods=["POST"])
def start_queue(queue_id):
    try:
        queue = AnalyzerService.start_queue(queue_id, actor=_actor())
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Analyzer run started", "queue": queue.to_dict()}


@lab_bp.route("/queues/<queue_id>/complete", methods=["POST"])
def complete_queue(queue_id):
    try:
        queue = AnalyzerService.complete_queue(queue_id, actor=_actor())
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Analyzer run completed", "queue": queue.to_dict()}


@lab_bp.route("/qc", methods=["GET"])
def list_qc():
    page, per_page = _page_args()
    return QCService.list_qc(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        analyzer_id=request.args.get("analyzer_id"),
        accession_id=request.args.get("accession_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/qc", methods=["POST"])
def create_qc():
    data = request.get_json(silent=True) or {}
    qc = QCService.create_qc(data)
    return {"message": "QC record created", "qc": qc.to_dict()}, 201


@lab_bp.route("/qc/<qc_id>", methods=["GET"])
def get_qc(qc_id):
    try:
        return {"qc": QCService.get_qc(qc_id)}
    except LabWorkflowError as exc:
        return _error(exc)


@lab_bp.route("/qc/<qc_id>", methods=["PUT"])
def update_qc(qc_id):
    data = request.get_json(silent=True) or {}
    try:
        qc = QCService.update_qc(qc_id, data)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "QC updated", "qc": qc.to_dict()}


@lab_bp.route("/qc/<qc_id>", methods=["DELETE"])
def delete_qc(qc_id):
    try:
        QCService.delete_qc(qc_id)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "QC deleted"}


@lab_bp.route("/qc/<qc_id>/evaluate", methods=["POST"])
def evaluate_qc(qc_id):
    try:
        qc = QCService.evaluate_qc(qc_id, actor=_actor())
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "QC evaluated", "qc": qc.to_dict()}


@lab_bp.route("/reviews", methods=["GET"])
def list_reviews():
    page, per_page = _page_args()
    return ReviewService.list_reviews(
        page=page,
        per_page=per_page,
        review_type=request.args.get("review_type"),
        status=request.args.get("status"),
        accession_id=request.args.get("accession_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/reviews/technician", methods=["POST"])
def create_technician_review():
    data = request.get_json(silent=True) or {}
    if not data.get("accession_id") or not data.get("reviewer"):
        return {"error": "accession_id and reviewer are required"}, 400
    review = ReviewService.create_technician_review(data)
    return {"message": "Technician review created", "review": review.to_dict()}, 201


@lab_bp.route("/reviews/pathologist", methods=["POST"])
def create_pathologist_review():
    data = request.get_json(silent=True) or {}
    if not data.get("accession_id") or not data.get("pathologist"):
        return {"error": "accession_id and pathologist are required"}, 400
    review = ReviewService.create_pathologist_review(data)
    return {"message": "Pathologist review created", "review": review.to_dict()}, 201


@lab_bp.route("/reviews/<review_id>", methods=["GET"])
def get_review(review_id):
    review_type = request.args.get("review_type", "technician")
    try:
        return {"review": ReviewService.get_review(review_id, review_type=review_type)}
    except LabWorkflowError as exc:
        return _error(exc)


@lab_bp.route("/reviews/<review_id>", methods=["DELETE"])
def delete_review(review_id):
    review_type = request.args.get("review_type", "technician")
    try:
        ReviewService.delete_review(review_id, review_type=review_type)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Review deleted"}


@lab_bp.route("/reviews/<review_id>/approve", methods=["POST"])
def approve_review(review_id):
    review_type = request.args.get("review_type", "technician")
    try:
        if review_type == "pathologist":
            review = ReviewService.approve_pathologist_review(review_id, actor=_actor())
        else:
            review = ReviewService.approve_technician_review(review_id, actor=_actor())
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Review approved", "review": review.to_dict()}


@lab_bp.route("/releases", methods=["GET"])
def list_releases():
    page, per_page = _page_args()
    return ReleaseService.list_releases(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        accession_id=request.args.get("accession_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/releases", methods=["POST"])
def create_release():
    data = request.get_json(silent=True) or {}
    if not data.get("accession_id"):
        return {"error": "accession_id is required"}, 400
    data["released_by"] = data.get("released_by") or _actor()
    try:
        release = ReleaseService.create_release(data)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Result released", "release": release.to_dict()}, 201


@lab_bp.route("/releases/<release_id>", methods=["GET"])
def get_release(release_id):
    try:
        return {"release": ReleaseService.get_release(release_id)}
    except LabWorkflowError as exc:
        return _error(exc)


@lab_bp.route("/releases/<release_id>", methods=["PUT"])
def update_release(release_id):
    data = request.get_json(silent=True) or {}
    try:
        release = ReleaseService.update_release(release_id, data)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Release updated", "release": release.to_dict()}


@lab_bp.route("/releases/<release_id>", methods=["DELETE"])
def delete_release(release_id):
    try:
        ReleaseService.delete_release(release_id)
    except LabWorkflowError as exc:
        return _error(exc)
    return {"message": "Release deleted"}


@lab_bp.route("/critical-results", methods=["GET"])
def list_critical_results():
    page, per_page = _page_args()
    return CriticalResultService.list_critical_results(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        accession_id=request.args.get("accession_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/critical-results", methods=["POST"])
def create_critical_result():
    data = request.get_json(silent=True) or {}
    if not data.get("accession_id") or not data.get("test_code"):
        return {"error": "accession_id and test_code are required"}, 400
    critical = CriticalResultService.create_critical_result(data)
    return {"message": "Critical result created", "critical_result": critical.to_dict()}, 201


@lab_bp.route("/delta-checks", methods=["GET"])
def list_delta_checks():
    page, per_page = _page_args()
    return DeltaCheckService.list_delta_checks(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        accession_id=request.args.get("accession_id"),
        q=request.args.get("q"),
    )


@lab_bp.route("/delta-checks", methods=["POST"])
def create_delta_check():
    data = request.get_json(silent=True) or {}
    if not data.get("accession_id") or not data.get("test_code"):
        return {"error": "accession_id and test_code are required"}, 400
    delta = DeltaCheckService.create_delta_check(data)
    return {"message": "Delta check created", "delta_check": delta.to_dict()}, 201
