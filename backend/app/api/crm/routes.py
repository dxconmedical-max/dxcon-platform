from flask import Blueprint, request

from app.services.crm_dashboard_service import CrmDashboardService
from app.services.crm_service import CrmError, CrmService
from app.services.quotation_service import QuotationError, QuotationService
from app.services.sales_contract_service import SalesContractError, SalesContractService


crm_bp = Blueprint("crm_api", __name__, url_prefix="/api/v1/crm")


def _page_args():
    return request.args.get("page", 1), request.args.get("per_page", 20)


def _error_response(exc):
    return {"error": exc.message}, exc.status_code


@crm_bp.route("/dashboard", methods=["GET"])
def crm_dashboard():
    return CrmDashboardService.get_dashboard()


@crm_bp.route("/leads", methods=["GET"])
def list_leads():
    page, per_page = _page_args()
    return CrmService.list_leads(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        pipeline_stage=request.args.get("pipeline_stage"),
        owner=request.args.get("owner"),
        q=request.args.get("q"),
    )


@crm_bp.route("/leads", methods=["POST"])
def create_lead():
    data = request.get_json(silent=True) or {}
    if not data.get("company_name") and not data.get("contact_person"):
        return {"error": "company_name or contact_person is required"}, 400
    lead = CrmService.create_lead(data)
    return {"message": "Lead created", "lead": lead.to_dict()}, 201


@crm_bp.route("/leads/<lead_id>", methods=["GET"])
def get_lead(lead_id):
    try:
        return {"lead": CrmService.get_lead(lead_id)}
    except CrmError as exc:
        return _error_response(exc)


@crm_bp.route("/leads/<lead_id>", methods=["PUT"])
def update_lead(lead_id):
    data = request.get_json(silent=True) or {}
    try:
        lead = CrmService.update_lead(lead_id, data)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Lead updated", "lead": lead.to_dict()}


@crm_bp.route("/leads/<lead_id>", methods=["DELETE"])
def delete_lead(lead_id):
    try:
        CrmService.delete_lead(lead_id)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Lead deleted"}


@crm_bp.route("/leads/<lead_id>/advance", methods=["POST"])
def advance_lead(lead_id):
    try:
        lead = CrmService.advance_lead_stage(lead_id)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Lead stage advanced", "lead": lead.to_dict()}


@crm_bp.route("/customers", methods=["GET"])
def list_customers():
    page, per_page = _page_args()
    return CrmService.list_customers(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        organization_id=request.args.get("organization_id"),
        owner=request.args.get("owner"),
        q=request.args.get("q"),
    )


@crm_bp.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return {"error": "name is required"}, 400
    customer = CrmService.create_customer(data)
    return {"message": "Customer created", "customer": customer.to_dict()}, 201


@crm_bp.route("/customers/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    try:
        return {"customer": CrmService.get_customer(customer_id)}
    except CrmError as exc:
        return _error_response(exc)


@crm_bp.route("/customers/<customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json(silent=True) or {}
    try:
        customer = CrmService.update_customer(customer_id, data)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Customer updated", "customer": customer.to_dict()}


@crm_bp.route("/customers/<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    try:
        CrmService.delete_customer(customer_id)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Customer deleted"}


@crm_bp.route("/opportunities", methods=["GET"])
def list_opportunities():
    page, per_page = _page_args()
    return CrmService.list_opportunities(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        pipeline_stage=request.args.get("pipeline_stage"),
        customer_id=request.args.get("customer_id"),
        owner=request.args.get("owner"),
        q=request.args.get("q"),
    )


@crm_bp.route("/opportunities", methods=["POST"])
def create_opportunity():
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return {"error": "title is required"}, 400
    opp = CrmService.create_opportunity(data)
    return {"message": "Opportunity created", "opportunity": opp.to_dict()}, 201


@crm_bp.route("/opportunities/<opportunity_id>", methods=["GET"])
def get_opportunity(opportunity_id):
    try:
        return {"opportunity": CrmService.get_opportunity(opportunity_id)}
    except CrmError as exc:
        return _error_response(exc)


@crm_bp.route("/opportunities/<opportunity_id>", methods=["PUT"])
def update_opportunity(opportunity_id):
    data = request.get_json(silent=True) or {}
    try:
        opp = CrmService.update_opportunity(opportunity_id, data)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Opportunity updated", "opportunity": opp.to_dict()}


@crm_bp.route("/opportunities/<opportunity_id>", methods=["DELETE"])
def delete_opportunity(opportunity_id):
    try:
        CrmService.delete_opportunity(opportunity_id)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Opportunity deleted"}


@crm_bp.route("/opportunities/<opportunity_id>/advance", methods=["POST"])
def advance_opportunity(opportunity_id):
    try:
        opp = CrmService.advance_opportunity(opportunity_id)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Opportunity stage advanced", "opportunity": opp.to_dict()}


@crm_bp.route("/activities", methods=["GET"])
def list_activities():
    page, per_page = _page_args()
    return CrmService.list_activities(
        page=page,
        per_page=per_page,
        activity_type=request.args.get("activity_type"),
        lead_id=request.args.get("lead_id"),
        customer_id=request.args.get("customer_id"),
        opportunity_id=request.args.get("opportunity_id"),
        owner=request.args.get("owner"),
        q=request.args.get("q"),
    )


@crm_bp.route("/activities", methods=["POST"])
def create_activity():
    data = request.get_json(silent=True) or {}
    if not data.get("activity_type") or not data.get("subject"):
        return {"error": "activity_type and subject are required"}, 400
    activity = CrmService.create_activity(data)
    return {"message": "Activity created", "activity": activity.to_dict()}, 201


@crm_bp.route("/activities/<activity_id>", methods=["GET"])
def get_activity(activity_id):
    try:
        return {"activity": CrmService.get_activity(activity_id)}
    except CrmError as exc:
        return _error_response(exc)


@crm_bp.route("/activities/<activity_id>", methods=["PUT"])
def update_activity(activity_id):
    data = request.get_json(silent=True) or {}
    try:
        activity = CrmService.update_activity(activity_id, data)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Activity updated", "activity": activity.to_dict()}


@crm_bp.route("/activities/<activity_id>", methods=["DELETE"])
def delete_activity(activity_id):
    try:
        CrmService.delete_activity(activity_id)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Activity deleted"}


@crm_bp.route("/pipelines", methods=["GET"])
def list_pipelines():
    page, per_page = _page_args()
    return CrmService.list_pipelines(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        q=request.args.get("q"),
    )


@crm_bp.route("/pipelines", methods=["POST"])
def create_pipeline():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return {"error": "name is required"}, 400
    pipeline = CrmService.create_pipeline(data)
    return {"message": "Pipeline created", "pipeline": pipeline.to_dict()}, 201


@crm_bp.route("/pipelines/<pipeline_id>", methods=["GET"])
def get_pipeline(pipeline_id):
    try:
        return {"pipeline": CrmService.get_pipeline(pipeline_id)}
    except CrmError as exc:
        return _error_response(exc)


@crm_bp.route("/pipelines/<pipeline_id>", methods=["PUT"])
def update_pipeline(pipeline_id):
    data = request.get_json(silent=True) or {}
    try:
        pipeline = CrmService.update_pipeline(pipeline_id, data)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Pipeline updated", "pipeline": pipeline.to_dict()}


@crm_bp.route("/pipelines/<pipeline_id>", methods=["DELETE"])
def delete_pipeline(pipeline_id):
    try:
        CrmService.delete_pipeline(pipeline_id)
    except CrmError as exc:
        return _error_response(exc)
    return {"message": "Pipeline deleted"}


@crm_bp.route("/quotations", methods=["GET"])
def list_quotations():
    page, per_page = _page_args()
    return QuotationService.list_quotations(
        page=page,
        per_page=per_page,
        approval_status=request.args.get("approval_status"),
        customer_id=request.args.get("customer_id"),
        opportunity_id=request.args.get("opportunity_id"),
        owner=request.args.get("owner"),
        q=request.args.get("q"),
    )


@crm_bp.route("/quotations", methods=["POST"])
def create_quotation():
    data = request.get_json(silent=True) or {}
    try:
        quotation = QuotationService.create_quotation(data)
    except QuotationError as exc:
        return _error_response(exc)
    return {"message": "Quotation created", "quotation": quotation.to_dict()}, 201


@crm_bp.route("/quotations/generate", methods=["POST"])
def generate_quotation():
    data = request.get_json(silent=True) or {}
    try:
        quotation = QuotationService.generate_quotation(data)
    except QuotationError as exc:
        return _error_response(exc)
    return {"message": "Quotation generated", "quotation": quotation.to_dict()}, 201


@crm_bp.route("/quotations/<quotation_id>", methods=["GET"])
def get_quotation(quotation_id):
    try:
        return {"quotation": QuotationService.get_quotation(quotation_id)}
    except QuotationError as exc:
        return _error_response(exc)


@crm_bp.route("/quotations/<quotation_id>", methods=["PUT"])
def update_quotation(quotation_id):
    data = request.get_json(silent=True) or {}
    try:
        quotation = QuotationService.update_quotation(quotation_id, data)
    except QuotationError as exc:
        return _error_response(exc)
    return {"message": "Quotation updated", "quotation": quotation.to_dict()}


@crm_bp.route("/quotations/<quotation_id>", methods=["DELETE"])
def delete_quotation(quotation_id):
    try:
        QuotationService.delete_quotation(quotation_id)
    except QuotationError as exc:
        return _error_response(exc)
    return {"message": "Quotation deleted"}


@crm_bp.route("/quotations/<quotation_id>/submit", methods=["POST"])
def submit_quotation(quotation_id):
    try:
        quotation = QuotationService.submit_for_approval(quotation_id)
    except QuotationError as exc:
        return _error_response(exc)
    return {"message": "Quotation submitted", "quotation": quotation.to_dict()}


@crm_bp.route("/quotations/<quotation_id>/approve", methods=["POST"])
def approve_quotation(quotation_id):
    try:
        quotation = QuotationService.approve_quotation(quotation_id)
    except QuotationError as exc:
        return _error_response(exc)
    return {"message": "Quotation approved", "quotation": quotation.to_dict()}


@crm_bp.route("/contracts", methods=["GET"])
def list_contracts():
    page, per_page = _page_args()
    return SalesContractService.list_contracts(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        contract_type=request.args.get("contract_type"),
        customer_id=request.args.get("customer_id"),
        organization_id=request.args.get("organization_id"),
        owner=request.args.get("owner"),
        q=request.args.get("q"),
    )


@crm_bp.route("/contracts", methods=["POST"])
def create_contract():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("contract_type"):
        return {"error": "title and contract_type are required"}, 400
    try:
        contract = SalesContractService.create_contract(data)
    except SalesContractError as exc:
        return _error_response(exc)
    return {"message": "Contract created", "contract": contract.to_dict()}, 201


@crm_bp.route("/contracts/<contract_id>", methods=["GET"])
def get_contract(contract_id):
    try:
        return {"contract": SalesContractService.get_contract(contract_id)}
    except SalesContractError as exc:
        return _error_response(exc)


@crm_bp.route("/contracts/<contract_id>", methods=["PUT"])
def update_contract(contract_id):
    data = request.get_json(silent=True) or {}
    try:
        contract = SalesContractService.update_contract(contract_id, data)
    except SalesContractError as exc:
        return _error_response(exc)
    return {"message": "Contract updated", "contract": contract.to_dict()}


@crm_bp.route("/contracts/<contract_id>", methods=["DELETE"])
def delete_contract(contract_id):
    try:
        SalesContractService.delete_contract(contract_id)
    except SalesContractError as exc:
        return _error_response(exc)
    return {"message": "Contract deleted"}


@crm_bp.route("/contracts/expiring", methods=["GET"])
def expiring_contracts():
    within_days = int(request.args.get("within_days", 30))
    return {
        "count": len(SalesContractService.expiring_contracts(within_days)),
        "contracts": SalesContractService.expiring_contracts(within_days),
    }
