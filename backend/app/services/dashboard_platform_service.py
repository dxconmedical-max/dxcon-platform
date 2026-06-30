import json
from datetime import datetime

from app.core.statuses import (
    DASHBOARD_ROLE_ADMIN,
    DASHBOARD_ROLE_CLINIC,
    DASHBOARD_ROLE_COLLECTOR,
    DASHBOARD_ROLE_EXECUTIVE,
    DASHBOARD_ROLE_LAB,
    DASHBOARD_ROLE_PARTNER,
    WIDGET_TYPE_COLLECTORS,
    WIDGET_TYPE_CRITICAL_RESULTS,
    WIDGET_TYPE_HEAT_MAP,
    WIDGET_TYPE_LABORATORIES,
    WIDGET_TYPE_ORDERS,
    WIDGET_TYPE_PARTNER_REVENUE,
    WIDGET_TYPE_PENDING_REVIEWS,
    WIDGET_TYPE_REVENUE,
    WIDGET_TYPE_SAMPLES,
    WIDGET_TYPE_TOP_TESTS,
    WIDGET_TYPE_TRANSPORT_TIMELINE,
)
from app.extensions.db import db
from app.models.reporting_platform import DashboardLayout, DashboardWidget
from app.services.analytics_engine_service import (
    CollectorAnalyticsService,
    LabAnalyticsService,
    PartnerAnalyticsService,
    RevenueAnalyticsService,
    SystemAnalyticsService,
    TransportAnalyticsService,
)
from app.services.kpi_engine_service import KPIEngineService
from app.services.reporting_service import ExecutiveDashboardService, ReportingService


DEFAULT_WIDGETS = [
    (WIDGET_TYPE_REVENUE, "Revenue", DASHBOARD_ROLE_EXECUTIVE),
    (WIDGET_TYPE_ORDERS, "Orders", DASHBOARD_ROLE_EXECUTIVE),
    (WIDGET_TYPE_SAMPLES, "Samples", DASHBOARD_ROLE_EXECUTIVE),
    (WIDGET_TYPE_COLLECTORS, "Collectors", DASHBOARD_ROLE_EXECUTIVE),
    (WIDGET_TYPE_LABORATORIES, "Laboratories", DASHBOARD_ROLE_LAB),
    (WIDGET_TYPE_TOP_TESTS, "Top Tests", DASHBOARD_ROLE_LAB),
    (WIDGET_TYPE_PARTNER_REVENUE, "Partner Revenue", DASHBOARD_ROLE_PARTNER),
    (WIDGET_TYPE_HEAT_MAP, "Heat Map", DASHBOARD_ROLE_ADMIN),
    (WIDGET_TYPE_TRANSPORT_TIMELINE, "Transport Timeline", DASHBOARD_ROLE_COLLECTOR),
    (WIDGET_TYPE_PENDING_REVIEWS, "Pending Reviews", DASHBOARD_ROLE_LAB),
    (WIDGET_TYPE_CRITICAL_RESULTS, "Critical Results", DASHBOARD_ROLE_LAB),
]


class DashboardPlatformService:

    @staticmethod
    def ensure_default_widgets():
        if DashboardWidget.query.first():
            return
        for idx, (widget_type, title, role) in enumerate(DEFAULT_WIDGETS):
            db.session.add(
                DashboardWidget(
                    widget_code=f"WGT-{widget_type}",
                    widget_type=widget_type,
                    title=title,
                    dashboard_role=role,
                    sort_order=idx,
                )
            )
        for role in [
            DASHBOARD_ROLE_EXECUTIVE,
            DASHBOARD_ROLE_ADMIN,
            DASHBOARD_ROLE_LAB,
            DASHBOARD_ROLE_CLINIC,
            DASHBOARD_ROLE_PARTNER,
            DASHBOARD_ROLE_COLLECTOR,
        ]:
            db.session.add(
                DashboardLayout(
                    layout_code=f"LYT-{role}",
                    dashboard_role=role,
                    name=f"{role.title()} Dashboard",
                    is_default=True,
                )
            )
        db.session.commit()

    @staticmethod
    def _paginate(items, page, page_size):
        total = len(items)
        offset = (page - 1) * page_size
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items[offset : offset + page_size],
        }

    @staticmethod
    def _build_widget_data(widget_type, date_from=None, date_to=None):
        kpi = KPIEngineService.compute_daily(anchor=date_to, persist=False)
        metrics = kpi["metrics"]
        if widget_type == WIDGET_TYPE_REVENUE:
            return RevenueAnalyticsService.aggregate(date_from, date_to)["summary"]
        if widget_type == WIDGET_TYPE_ORDERS:
            return {"orders": metrics.get("ORDERS", 0)}
        if widget_type == WIDGET_TYPE_SAMPLES:
            return {"samples": metrics.get("SAMPLES", 0)}
        if widget_type == WIDGET_TYPE_COLLECTORS:
            return CollectorAnalyticsService.aggregate(date_from, date_to, page_size=5)
        if widget_type == WIDGET_TYPE_LABORATORIES:
            return SystemAnalyticsService.aggregate(date_from, date_to)
        if widget_type == WIDGET_TYPE_TOP_TESTS:
            return LabAnalyticsService.aggregate(date_from, date_to)["summary"]
        if widget_type == WIDGET_TYPE_PARTNER_REVENUE:
            return PartnerAnalyticsService.aggregate(date_from, date_to, page_size=5)
        if widget_type == WIDGET_TYPE_HEAT_MAP:
            return {"cells": [{"x": i, "y": j, "value": (i + j) % 10} for i in range(5) for j in range(5)]}
        if widget_type == WIDGET_TYPE_TRANSPORT_TIMELINE:
            return TransportAnalyticsService.aggregate(date_from, date_to, page_size=10)
        if widget_type == WIDGET_TYPE_PENDING_REVIEWS:
            return {"pending_reviews": kpi["metrics"].get("pending_reviews", 0)}
        if widget_type == WIDGET_TYPE_CRITICAL_RESULTS:
            return {"critical_result_rate": metrics.get("CRITICAL_RESULTS", 0)}
        return {}

    @staticmethod
    def get_dashboard(role, date_from=None, date_to=None, page=1, page_size=20, filters=None):
        DashboardPlatformService.ensure_default_widgets()
        filters = filters or {}
        widgets = DashboardWidget.query.filter_by(dashboard_role=role, is_active=True).order_by(
            DashboardWidget.sort_order
        ).all()
        widget_payloads = []
        for widget in widgets:
            widget_payloads.append(
                {
                    "widget": widget.to_dict(),
                    "data": DashboardPlatformService._build_widget_data(
                        widget.widget_type, date_from, date_to
                    ),
                }
            )

        base = {
            "dashboard_role": role,
            "generated_at": datetime.utcnow().isoformat(),
            "filters": filters,
            "widgets": DashboardPlatformService._paginate(widget_payloads, page, page_size)["items"],
            "pagination": {
                "total": len(widget_payloads),
                "page": page,
                "page_size": page_size,
            },
        }

        if role == DASHBOARD_ROLE_EXECUTIVE:
            base["executive"] = ExecutiveDashboardService.get_dashboard(date_from, date_to)
        elif role == DASHBOARD_ROLE_ADMIN:
            base["system"] = SystemAnalyticsService.aggregate(date_from, date_to)
            base["operations"] = ReportingService.get_operations_report(date_from, date_to)
        elif role == DASHBOARD_ROLE_LAB:
            base["lab"] = LabAnalyticsService.aggregate(date_from, date_to)
        elif role == DASHBOARD_ROLE_CLINIC:
            from app.services.analytics_engine_service import ClinicAnalyticsService

            base["clinic"] = ClinicAnalyticsService.aggregate(date_from, date_to, page=page, page_size=page_size)
        elif role == DASHBOARD_ROLE_PARTNER:
            base["partner"] = PartnerAnalyticsService.aggregate(
                date_from, date_to, partner_id=filters.get("partner_id"), page=page, page_size=page_size
            )
        elif role == DASHBOARD_ROLE_COLLECTOR:
            base["collector"] = CollectorAnalyticsService.aggregate(
                date_from, date_to, collector_id=filters.get("collector_id"), page=page, page_size=page_size
            )
            base["transport"] = TransportAnalyticsService.aggregate(date_from, date_to, page=page, page_size=page_size)

        return base
