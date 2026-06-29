from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import func

from app.core.statuses import (
    CRM_CONTRACT_ACTIVE,
    CRM_OPPORTUNITY_WON,
    CRM_PIPELINE_STAGES,
    CRM_QUOTATION_DRAFT,
    CRM_QUOTATION_SENT,
)
from app.models.crm_lead import CrmLead
from app.models.crm_organization import Customer
from app.models.crm_pipeline import Opportunity
from app.models.crm_quotation import Quotation
from app.models.crm_sales_contract import SalesContract
from app.services.sales_contract_service import SalesContractService


class CrmDashboardService:
    @staticmethod
    def get_dashboard():
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        lead_funnel = {}
        for stage in CRM_PIPELINE_STAGES:
            lead_count = CrmLead.query.filter_by(pipeline_stage=stage).count()
            opp_count = Opportunity.query.filter_by(pipeline_stage=stage).count()
            lead_funnel[stage] = lead_count + opp_count

        total_leads = CrmLead.query.count()
        won_opps = Opportunity.query.filter_by(status=CRM_OPPORTUNITY_WON).count()
        lost_opps = Opportunity.query.filter_by(status="LOST").count()
        closed = won_opps + lost_opps
        conversion_rate = round((won_opps / closed) * 100, 2) if closed else 0

        forecast_rows = (
            Opportunity.query.filter(Opportunity.status != "LOST")
            .with_entities(func.sum(Opportunity.amount).label("total"))
            .scalar()
            or 0
        )

        monthly_sales = (
            Opportunity.query.filter(
                Opportunity.status == CRM_OPPORTUNITY_WON,
                Opportunity.updated_at >= month_start,
            )
            .with_entities(func.sum(Opportunity.amount).label("total"))
            .scalar()
            or 0
        )

        top_customers = (
            Opportunity.query.filter(Opportunity.customer_id.isnot(None))
            .with_entities(
                Opportunity.customer_id,
                func.sum(Opportunity.amount).label("revenue"),
            )
            .group_by(Opportunity.customer_id)
            .order_by(func.sum(Opportunity.amount).desc())
            .limit(5)
            .all()
        )
        top_customer_payload = []
        for customer_id, revenue in top_customers:
            customer = Customer.query.get(customer_id)
            top_customer_payload.append(
                {
                    "customer_id": customer_id,
                    "customer_name": customer.name if customer else None,
                    "revenue": float(revenue or 0),
                }
            )

        owner_rows = (
            Opportunity.query.with_entities(
                Opportunity.owner,
                func.sum(Opportunity.amount).label("revenue"),
            )
            .filter(Opportunity.owner.isnot(None))
            .group_by(Opportunity.owner)
            .order_by(func.sum(Opportunity.amount).desc())
            .limit(5)
            .all()
        )
        top_sales = [
            {"owner": owner, "revenue": float(revenue or 0)} for owner, revenue in owner_rows
        ]

        open_quotations = Quotation.query.filter(
            Quotation.approval_status.in_([CRM_QUOTATION_DRAFT, CRM_QUOTATION_SENT])
        ).count()

        expiring_contracts = SalesContractService.expiring_contracts(within_days=30)

        return {
            "summary": {
                "total_leads": total_leads,
                "total_customers": Customer.query.count(),
                "total_opportunities": Opportunity.query.count(),
                "open_quotations": open_quotations,
                "active_contracts": SalesContract.query.filter_by(
                    status=CRM_CONTRACT_ACTIVE
                ).count(),
                "conversion_rate": conversion_rate,
                "revenue_forecast": float(forecast_rows),
                "monthly_sales": float(monthly_sales),
            },
            "lead_funnel": lead_funnel,
            "top_customers": top_customer_payload,
            "top_sales": top_sales,
            "open_quotations_count": open_quotations,
            "expiring_contracts": expiring_contracts,
            "generated_at": now.isoformat(),
        }
