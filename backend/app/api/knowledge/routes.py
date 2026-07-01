from flask import Blueprint, request

from app.services.knowledge_engine_service import (
    BiomarkerService,
    CorrelationService,
    DiseaseMappingService,
    GuidelinePackService,
    KnowledgeError,
    KnowledgeSearchService,
    ReferenceLibraryService,
)


def _page_args():
    return (
        max(int(request.args.get("page", 1)), 1),
        min(max(int(request.args.get("page_size", 50)), 1), 200),
    )


def _error(exc):
    return {"error": exc.message}, exc.status_code


knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/api/v1/knowledge")
guidelines_bp = Blueprint("guidelines", __name__, url_prefix="/api/v1/guidelines")
biomarkers_bp = Blueprint("biomarkers", __name__, url_prefix="/api/v1/biomarkers")
diseases_bp = Blueprint("diseases", __name__, url_prefix="/api/v1/diseases")
correlations_bp = Blueprint("correlations", __name__, url_prefix="/api/v1/correlations")


@knowledge_bp.route("", methods=["GET"])
def search_knowledge():
    page, page_size = _page_args()
    return KnowledgeSearchService.search(
        query=request.args.get("q") or request.args.get("query"),
        category=request.args.get("category"),
        source_pack=request.args.get("source_pack") or request.args.get("pack"),
        page=page,
        page_size=page_size,
    )


@knowledge_bp.route("", methods=["POST"])
def create_knowledge():
    data = request.get_json(silent=True) or {}
    if not data.get("title") and not data.get("content"):
        return {"error": "title or content is required"}, 400
    return KnowledgeSearchService.create(data), 201


@knowledge_bp.route("/<knowledge_id>", methods=["GET"])
def get_knowledge(knowledge_id):
    try:
        return KnowledgeSearchService.get(knowledge_id)
    except KnowledgeError as exc:
        return _error(exc)


@knowledge_bp.route("/references", methods=["GET"])
def list_references():
    return ReferenceLibraryService.list_references(
        test_code=request.args.get("test_code"),
        source_pack=request.args.get("source_pack") or request.args.get("pack"),
    )


@guidelines_bp.route("", methods=["GET"])
def list_guidelines():
    page, page_size = _page_args()
    return GuidelinePackService.list_guidelines(
        pack_source=request.args.get("pack") or request.args.get("pack_source"),
        version=request.args.get("version"),
        page=page,
        page_size=page_size,
    )


@guidelines_bp.route("", methods=["POST"])
def create_guideline():
    data = request.get_json(silent=True) or {}
    try:
        return GuidelinePackService.create(data), 201
    except KnowledgeError as exc:
        return _error(exc)


@guidelines_bp.route("/packs", methods=["GET"])
def list_packs():
    return GuidelinePackService.list_packs()


@guidelines_bp.route("/<guideline_id>", methods=["GET"])
def get_guideline(guideline_id):
    try:
        return GuidelinePackService.get(guideline_id)
    except KnowledgeError as exc:
        return _error(exc)


@biomarkers_bp.route("", methods=["GET"])
def list_biomarkers():
    page, page_size = _page_args()
    return BiomarkerService.list_biomarkers(
        query=request.args.get("q") or request.args.get("query"),
        page=page,
        page_size=page_size,
    )


@biomarkers_bp.route("/<biomarker_code>", methods=["GET"])
def get_biomarker(biomarker_code):
    try:
        return BiomarkerService.get_by_code(biomarker_code)
    except KnowledgeError as exc:
        return _error(exc)


@biomarkers_bp.route("/<biomarker_code>/relationships", methods=["GET"])
def biomarker_relationships(biomarker_code):
    try:
        return BiomarkerService.relationships(biomarker_code)
    except KnowledgeError as exc:
        return _error(exc)


@diseases_bp.route("", methods=["GET"])
def list_diseases():
    page, page_size = _page_args()
    return DiseaseMappingService.list_diseases(
        query=request.args.get("q") or request.args.get("query"),
        page=page,
        page_size=page_size,
    )


@diseases_bp.route("/<disease_code>", methods=["GET"])
def get_disease(disease_code):
    try:
        return DiseaseMappingService.get_by_code(disease_code)
    except KnowledgeError as exc:
        return _error(exc)


@diseases_bp.route("/<disease_code>/tests", methods=["GET"])
def disease_tests(disease_code):
    try:
        return DiseaseMappingService.tests_for_disease(disease_code)
    except KnowledgeError as exc:
        return _error(exc)


@diseases_bp.route("/by-test/<test_code>", methods=["GET"])
def diseases_by_test(test_code):
    return DiseaseMappingService.diseases_for_test(test_code)


@correlations_bp.route("/match", methods=["POST"])
def correlate_match():
    data = request.get_json(silent=True) or {}
    if not data.get("items"):
        return {"error": "items is required"}, 400
    return CorrelationService.match_markers(data)


@correlations_bp.route("/evaluate", methods=["POST"])
def correlate_evaluate():
    data = request.get_json(silent=True) or {}
    if not data.get("items"):
        return {"error": "items is required"}, 400
    try:
        return CorrelationService.evaluate_chains(data)
    except KnowledgeError as exc:
        return _error(exc)
