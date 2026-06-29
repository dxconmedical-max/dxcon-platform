from datetime import datetime

from app.core.pagination import paginate_query, pagination_payload
from app.core.statuses import (
    CRM_CUSTOMER_ACTIVE,
    CRM_LEAD_NEW,
    CRM_OPPORTUNITY_OPEN,
    CRM_ORG_ACTIVE,
    CRM_PIPELINE_STAGE_LEAD,
    CRM_PIPELINE_STAGES,
)
from app.extensions.db import db
from app.models.crm_activity import Activity
from app.models.crm_lead import CrmLead
from app.models.crm_organization import ContactPerson, Customer, Organization
from app.models.crm_pipeline import Opportunity, PipelineStage, SalesPipeline
from app.services.crm_helpers import (
    apply_filters,
    apply_search,
    generate_code,
    get_or_404,
    list_resource,
    parse_date,
    parse_datetime,
)


class CrmError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CrmService:
    @staticmethod
    def _next_stage(current):
        if current not in CRM_PIPELINE_STAGES:
            return CRM_PIPELINE_STAGE_LEAD
        idx = CRM_PIPELINE_STAGES.index(current)
        if idx >= len(CRM_PIPELINE_STAGES) - 1:
            return current
        return CRM_PIPELINE_STAGES[idx + 1]

    @staticmethod
    def list_leads(page=1, per_page=20, status=None, pipeline_stage=None, owner=None, q=None):
        filters = {
            "status": status,
            "pipeline_stage": pipeline_stage,
            "owner": owner,
            "q": q,
        }
        return list_resource(
            CrmLead,
            lambda item: item.to_dict(),
            search_fields=["lead_code", "company_name", "contact_person", "email", "phone"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_lead(data):
        lead = CrmLead(
            lead_code=data.get("lead_code") or generate_code("LEAD"),
            company_name=data.get("company_name"),
            contact_person=data.get("contact_person"),
            phone=data.get("phone"),
            email=data.get("email"),
            lead_source=data.get("lead_source"),
            organization_id=data.get("organization_id"),
            pipeline_stage=data.get("pipeline_stage", CRM_PIPELINE_STAGE_LEAD),
            status=data.get("status", CRM_LEAD_NEW),
            estimated_revenue=float(data.get("estimated_revenue") or 0),
            owner=data.get("owner"),
            notes=data.get("notes"),
        )
        db.session.add(lead)
        db.session.commit()
        return lead

    @staticmethod
    def get_lead(lead_id):
        return get_or_404(CrmLead, lead_id, CrmError).to_dict()

    @staticmethod
    def update_lead(lead_id, data):
        lead = get_or_404(CrmLead, lead_id, CrmError)
        for field in (
            "company_name",
            "contact_person",
            "phone",
            "email",
            "lead_source",
            "organization_id",
            "pipeline_stage",
            "status",
            "owner",
            "notes",
        ):
            if field in data:
                setattr(lead, field, data[field])
        if "estimated_revenue" in data:
            lead.estimated_revenue = float(data["estimated_revenue"] or 0)
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        return lead

    @staticmethod
    def delete_lead(lead_id):
        lead = get_or_404(CrmLead, lead_id, CrmError)
        db.session.delete(lead)
        db.session.commit()

    @staticmethod
    def advance_lead_stage(lead_id):
        lead = get_or_404(CrmLead, lead_id, CrmError)
        lead.pipeline_stage = CrmService._next_stage(lead.pipeline_stage)
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        return lead

    @staticmethod
    def list_customers(page=1, per_page=20, status=None, organization_id=None, owner=None, q=None):
        filters = {
            "status": status,
            "organization_id": organization_id,
            "owner": owner,
            "q": q,
        }
        return list_resource(
            Customer,
            lambda item: item.to_dict(),
            search_fields=["customer_code", "name", "email", "phone"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_customer(data):
        customer = Customer(
            customer_code=data.get("customer_code") or generate_code("CUST"),
            name=data["name"],
            organization_id=data.get("organization_id"),
            customer_type=data.get("customer_type", "B2B"),
            email=data.get("email"),
            phone=data.get("phone"),
            billing_address=data.get("billing_address"),
            owner=data.get("owner"),
            status=data.get("status", CRM_CUSTOMER_ACTIVE),
        )
        db.session.add(customer)
        db.session.commit()
        return customer

    @staticmethod
    def get_customer(customer_id):
        return get_or_404(Customer, customer_id, CrmError).to_dict()

    @staticmethod
    def update_customer(customer_id, data):
        customer = get_or_404(Customer, customer_id, CrmError)
        for field in (
            "name",
            "organization_id",
            "customer_type",
            "email",
            "phone",
            "billing_address",
            "owner",
            "status",
        ):
            if field in data:
                setattr(customer, field, data[field])
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        return customer

    @staticmethod
    def delete_customer(customer_id):
        customer = get_or_404(Customer, customer_id, CrmError)
        db.session.delete(customer)
        db.session.commit()

    @staticmethod
    def list_organizations(page=1, per_page=20, status=None, org_type=None, owner=None, q=None):
        filters = {"status": status, "org_type": org_type, "owner": owner, "q": q}
        return list_resource(
            Organization,
            lambda item: item.to_dict(),
            search_fields=["org_code", "name", "email", "phone", "tax_code"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_organization(data):
        org = Organization(
            org_code=data.get("org_code") or generate_code("ORG"),
            name=data["name"],
            org_type=data.get("org_type", "CORPORATE"),
            industry=data.get("industry"),
            tax_code=data.get("tax_code"),
            address=data.get("address"),
            phone=data.get("phone"),
            email=data.get("email"),
            owner=data.get("owner"),
            status=data.get("status", CRM_ORG_ACTIVE),
        )
        db.session.add(org)
        db.session.commit()
        return org

    @staticmethod
    def get_organization(org_id):
        return get_or_404(Organization, org_id, CrmError).to_dict()

    @staticmethod
    def update_organization(org_id, data):
        org = get_or_404(Organization, org_id, CrmError)
        for field in (
            "name",
            "org_type",
            "industry",
            "tax_code",
            "address",
            "phone",
            "email",
            "owner",
            "status",
        ):
            if field in data:
                setattr(org, field, data[field])
        org.updated_at = datetime.utcnow()
        db.session.commit()
        return org

    @staticmethod
    def delete_organization(org_id):
        org = get_or_404(Organization, org_id, CrmError)
        db.session.delete(org)
        db.session.commit()

    @staticmethod
    def list_opportunities(
        page=1, per_page=20, status=None, pipeline_stage=None, customer_id=None, owner=None, q=None
    ):
        filters = {
            "status": status,
            "pipeline_stage": pipeline_stage,
            "customer_id": customer_id,
            "owner": owner,
            "q": q,
        }
        return list_resource(
            Opportunity,
            lambda item: item.to_dict(),
            search_fields=["opportunity_code", "title", "owner"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_opportunity(data):
        opp = Opportunity(
            opportunity_code=data.get("opportunity_code") or generate_code("OPP"),
            title=data["title"],
            lead_id=data.get("lead_id"),
            customer_id=data.get("customer_id"),
            organization_id=data.get("organization_id"),
            pipeline_id=data.get("pipeline_id"),
            pipeline_stage=data.get("pipeline_stage", CRM_PIPELINE_STAGE_LEAD),
            amount=float(data.get("amount") or 0),
            currency=data.get("currency", "VND"),
            expected_close_date=parse_date(data.get("expected_close_date")),
            status=data.get("status", CRM_OPPORTUNITY_OPEN),
            owner=data.get("owner"),
            notes=data.get("notes"),
        )
        db.session.add(opp)
        db.session.commit()
        return opp

    @staticmethod
    def get_opportunity(opportunity_id):
        return get_or_404(Opportunity, opportunity_id, CrmError).to_dict()

    @staticmethod
    def update_opportunity(opportunity_id, data):
        opp = get_or_404(Opportunity, opportunity_id, CrmError)
        for field in (
            "title",
            "lead_id",
            "customer_id",
            "organization_id",
            "pipeline_id",
            "pipeline_stage",
            "currency",
            "status",
            "owner",
            "notes",
        ):
            if field in data:
                setattr(opp, field, data[field])
        if "amount" in data:
            opp.amount = float(data["amount"] or 0)
        if "expected_close_date" in data:
            opp.expected_close_date = parse_date(data.get("expected_close_date"))
        opp.updated_at = datetime.utcnow()
        db.session.commit()
        return opp

    @staticmethod
    def delete_opportunity(opportunity_id):
        opp = get_or_404(Opportunity, opportunity_id, CrmError)
        db.session.delete(opp)
        db.session.commit()

    @staticmethod
    def advance_opportunity(opportunity_id):
        opp = get_or_404(Opportunity, opportunity_id, CrmError)
        opp.pipeline_stage = CrmService._next_stage(opp.pipeline_stage)
        if opp.pipeline_stage == "WON":
            opp.status = "WON"
        elif opp.pipeline_stage == "LOST":
            opp.status = "LOST"
        opp.updated_at = datetime.utcnow()
        db.session.commit()
        return opp

    @staticmethod
    def list_activities(
        page=1,
        per_page=20,
        activity_type=None,
        lead_id=None,
        customer_id=None,
        opportunity_id=None,
        owner=None,
        q=None,
    ):
        query = Activity.query
        if activity_type:
            query = query.filter(Activity.activity_type == activity_type)
        if lead_id:
            query = query.filter(Activity.lead_id == lead_id)
        if customer_id:
            query = query.filter(Activity.customer_id == customer_id)
        if opportunity_id:
            query = query.filter(Activity.opportunity_id == opportunity_id)
        if owner:
            query = query.filter(Activity.owner == owner)
        if q:
            query = apply_search(
                query, Activity, q, ["subject", "description", "owner", "activity_type"]
            )
        query = query.order_by(Activity.created_at.desc())
        result = paginate_query(query, page=page, per_page=per_page)
        return pagination_payload(result["items"], result["pagination"], serializer=lambda a: a.to_dict())

    @staticmethod
    def create_activity(data):
        activity = Activity(
            activity_type=data["activity_type"],
            subject=data["subject"],
            description=data.get("description"),
            related_type=data.get("related_type"),
            related_id=data.get("related_id"),
            lead_id=data.get("lead_id"),
            customer_id=data.get("customer_id"),
            opportunity_id=data.get("opportunity_id"),
            due_date=parse_datetime(data.get("due_date")),
            reminder_at=parse_datetime(data.get("reminder_at")),
            is_completed=bool(data.get("is_completed", False)),
            attachment_url=data.get("attachment_url"),
            owner=data.get("owner"),
        )
        db.session.add(activity)
        db.session.commit()
        return activity

    @staticmethod
    def get_activity(activity_id):
        return get_or_404(Activity, activity_id, CrmError).to_dict()

    @staticmethod
    def update_activity(activity_id, data):
        activity = get_or_404(Activity, activity_id, CrmError)
        for field in (
            "activity_type",
            "subject",
            "description",
            "related_type",
            "related_id",
            "lead_id",
            "customer_id",
            "opportunity_id",
            "is_completed",
            "attachment_url",
            "owner",
        ):
            if field in data:
                setattr(activity, field, data[field])
        if "due_date" in data:
            activity.due_date = parse_datetime(data.get("due_date"))
        if "reminder_at" in data:
            activity.reminder_at = parse_datetime(data.get("reminder_at"))
        activity.updated_at = datetime.utcnow()
        db.session.commit()
        return activity

    @staticmethod
    def delete_activity(activity_id):
        activity = get_or_404(Activity, activity_id, CrmError)
        db.session.delete(activity)
        db.session.commit()

    @staticmethod
    def list_pipelines(page=1, per_page=20, status=None, q=None):
        filters = {"status": status, "q": q}
        return list_resource(
            SalesPipeline,
            lambda item: item.to_dict(),
            search_fields=["pipeline_code", "name"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_pipeline(data):
        pipeline = SalesPipeline(
            pipeline_code=data.get("pipeline_code") or generate_code("PIPE"),
            name=data["name"],
            description=data.get("description"),
            is_default=bool(data.get("is_default", False)),
            status=data.get("status", CRM_ORG_ACTIVE),
        )
        db.session.add(pipeline)
        db.session.flush()
        stages = data.get("stages") or [
            {"stage_code": stage, "name": stage.title(), "sort_order": idx}
            for idx, stage in enumerate(CRM_PIPELINE_STAGES)
        ]
        for idx, stage_data in enumerate(stages):
            stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_code=stage_data.get("stage_code", f"STAGE-{idx}"),
                name=stage_data.get("name", f"Stage {idx + 1}"),
                sort_order=int(stage_data.get("sort_order", idx)),
                win_probability=float(stage_data.get("win_probability", 0)),
                is_closed=bool(stage_data.get("is_closed", False)),
                is_won=bool(stage_data.get("is_won", False)),
            )
            db.session.add(stage)
        db.session.commit()
        return pipeline

    @staticmethod
    def get_pipeline(pipeline_id):
        pipeline = get_or_404(SalesPipeline, pipeline_id, CrmError)
        stages = (
            PipelineStage.query.filter_by(pipeline_id=pipeline.id)
            .order_by(PipelineStage.sort_order.asc())
            .all()
        )
        payload = pipeline.to_dict()
        payload["stages"] = [stage.to_dict() for stage in stages]
        return payload

    @staticmethod
    def update_pipeline(pipeline_id, data):
        pipeline = get_or_404(SalesPipeline, pipeline_id, CrmError)
        for field in ("name", "description", "is_default", "status"):
            if field in data:
                setattr(pipeline, field, data[field])
        db.session.commit()
        return pipeline

    @staticmethod
    def delete_pipeline(pipeline_id):
        pipeline = get_or_404(SalesPipeline, pipeline_id, CrmError)
        PipelineStage.query.filter_by(pipeline_id=pipeline.id).delete()
        db.session.delete(pipeline)
        db.session.commit()

    @staticmethod
    def ensure_default_pipeline():
        existing = SalesPipeline.query.filter_by(is_default=True).first()
        if existing:
            return existing
        return CrmService.create_pipeline(
            {
                "pipeline_code": "DEFAULT",
                "name": "Default Sales Pipeline",
                "is_default": True,
                "description": "Lead to Won/Lost workflow",
            }
        )
