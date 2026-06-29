from datetime import datetime

from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.commission_ledger import CommissionLedger
from app.models.invoice import Invoice
from app.models.marketplace_booking import MarketplaceBooking
from app.models.medical_order import MedicalOrder
from app.models.partner import Partner
from app.models.partner_settlement import PartnerSettlement
from app.models.result_file import ResultFile


class PartnerPortalError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PartnerDashboardService:

    @staticmethod
    def _get_partner_or_raise(partner_id):
        partner = Partner.query.get(partner_id)
        if not partner:
            raise PartnerPortalError("Partner not found", 404)
        return partner

    @staticmethod
    def get_dashboard(partner_id):
        partner = PartnerDashboardService._get_partner_or_raise(partner_id)
        orders = MedicalOrder.query.filter_by(partner_id=partner_id).all()
        bookings = MarketplaceBooking.query.filter_by(partner_id=partner_id).count()
        invoices = Invoice.query.filter_by(partner_id=partner_id).all()
        paid = [inv for inv in invoices if inv.billing_status == "PAID"]
        settlements = PartnerSettlement.query.filter_by(partner_id=partner_id).all()

        return {
            "partner": partner.to_dict(),
            "orders_total": len(orders),
            "orders_active": len(
                [o for o in orders if o.status not in ("COMPLETED", "CANCELLED", "REFUNDED", "REJECTED")]
            ),
            "bookings_total": bookings,
            "revenue_total": sum(inv.total_amount or 0 for inv in paid),
            "invoices_paid": len(paid),
            "settlements_total": len(settlements),
            "recent_orders": [
                order.to_dict()
                for order in sorted(orders, key=lambda o: o.created_at or datetime.min, reverse=True)[:5]
            ],
        }


class PartnerOrderService:

    @staticmethod
    def list_orders(partner_id, status=None):
        query = MedicalOrder.query.filter_by(partner_id=partner_id)
        if status:
            query = query.filter(MedicalOrder.status == status)
        orders = query.order_by(MedicalOrder.created_at.desc()).all()
        payload = []
        for order in orders:
            item = order.to_dict()
            booking = MarketplaceBooking.query.get(order.marketplace_booking_id)
            assignment = None
            if booking:
                assignment = BookingAssignment.query.filter_by(booking_id=booking.id).first()
            item["booking_code"] = booking.booking_code if booking else None
            item["assignment_status"] = assignment.assignment_status if assignment else None
            payload.append(item)
        return payload

    @staticmethod
    def get_order(partner_id, order_id):
        order = MedicalOrder.query.get(order_id)
        if not order or order.partner_id != partner_id:
            raise PartnerPortalError("Order not found for partner", 404)
        from app.services.order_workflow_service import OrderWorkflowService
        return OrderWorkflowService.get_order_detail(order_id)


class PartnerResultUploadService:

    @staticmethod
    def upload_result(partner_id, data, actor_email="SYSTEM"):
        order_id = data.get("medical_order_id")
        order = MedicalOrder.query.get(order_id)
        if not order or order.partner_id != partner_id:
            raise PartnerPortalError("Order not found for partner", 404)

        result_file = ResultFile(
            order_id=order.legacy_order_id or order.id,
            file_name=data.get("file_name", "result.pdf"),
            file_path=data.get("file_path", f"/uploads/partners/{partner_id}/{order.order_code}.pdf"),
            uploaded_by=actor_email,
        )
        db.session.add(result_file)
        db.session.commit()
        return result_file

    @staticmethod
    def list_results(partner_id):
        orders = MedicalOrder.query.filter_by(partner_id=partner_id).all()
        order_ids = [o.legacy_order_id or o.id for o in orders]
        if not order_ids:
            return []
        return ResultFile.query.filter(ResultFile.order_id.in_(order_ids)).all()


class PartnerSLAService:

    @staticmethod
    def get_sla_summary(partner_id):
        partner = Partner.query.get(partner_id)
        if not partner:
            raise PartnerPortalError("Partner not found", 404)

        orders = MedicalOrder.query.filter_by(partner_id=partner_id).all()
        completed = [o for o in orders if o.status == "COMPLETED"]
        on_time = len(completed)
        total = len(orders) or 1
        compliance_rate = round((on_time / total) * 100, 2)

        return {
            "partner_id": partner_id,
            "pickup_sla_minutes": partner.pickup_sla_minutes,
            "response_sla_minutes": partner.response_sla_minutes,
            "average_result_time_hours": partner.average_result_time_hours,
            "orders_total": len(orders),
            "orders_completed": len(completed),
            "sla_compliance_rate": compliance_rate,
            "breaches": max(len(orders) - len(completed), 0),
        }


class PartnerRevenueService:

    @staticmethod
    def get_revenue_summary(partner_id):
        invoices = Invoice.query.filter_by(partner_id=partner_id).all()
        paid = [inv for inv in invoices if inv.billing_status == "PAID"]
        refunded = [inv for inv in invoices if inv.billing_status == "REFUNDED"]
        commissions = CommissionLedger.query.filter_by(partner_id=partner_id, role_type="PARTNER").all()
        settlements = PartnerSettlement.query.filter_by(partner_id=partner_id).all()

        gross = sum(inv.total_amount or 0 for inv in paid)
        commission_total = sum(entry.commission_amount for entry in commissions)
        net = gross - commission_total

        return {
            "partner_id": partner_id,
            "gross_revenue": gross,
            "commission_total": commission_total,
            "net_revenue": net,
            "invoices_paid": len(paid),
            "invoices_refunded": len(refunded),
            "settlements_total": len(settlements),
            "settlements_paid": len([s for s in settlements if s.status == "PAID"]),
            "recent_invoices": [inv.to_dict() for inv in paid[:5]],
        }
