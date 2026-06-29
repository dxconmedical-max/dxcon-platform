from datetime import datetime

from sqlalchemy import or_

from app.core.statuses import MAPPING_ACTIVE, MARKETPLACE_VISIBLE_PARTNER_STATUSES
from app.extensions.db import db
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.partner_verification_item import PartnerVerificationItem
from app.services.partner_availability import PartnerAvailabilityService
from app.services.ranking_service import RankingService


class MarketplaceSearchService:

    SORT_OPTIONS = {
        "relevance",
        "price_asc",
        "price_desc",
        "rating_desc",
        "turnaround_asc",
    }

    @staticmethod
    def _partner_marketplace_dict(partner):
        return {
            "id": partner.id,
            "partner_code": partner.partner_code,
            "partner_type": partner.partner_type,
            "display_name": partner.display_name,
            "city": partner.city,
            "province": partner.province,
            "district": partner.district,
            "status": partner.status,
            "rating": partner.rating or 0.0,
            "review_count": partner.review_count or 0,
            "completed_orders": partner.completed_orders or 0,
        }

    @staticmethod
    def search(
        q=None,
        province=None,
        city=None,
        district=None,
        partner_type=None,
        home_collection=None,
        max_price=None,
        sort="relevance",
        date=None,
    ):
        if sort not in MarketplaceSearchService.SORT_OPTIONS:
            sort = "relevance"

        search_date = date or datetime.utcnow().strftime("%Y-%m-%d")

        query = (
            db.session.query(PartnerServiceMapping, Partner, DiagnosticService)
            .join(Partner, Partner.id == PartnerServiceMapping.partner_id)
            .join(
                DiagnosticService,
                DiagnosticService.id == PartnerServiceMapping.diagnostic_service_id,
            )
            .filter(PartnerServiceMapping.status == MAPPING_ACTIVE)
            .filter(DiagnosticService.is_active.is_(True))
            .filter(Partner.status.in_(MARKETPLACE_VISIBLE_PARTNER_STATUSES))
        )

        if q:
            term = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    DiagnosticService.name.ilike(term),
                    DiagnosticService.short_name.ilike(term),
                    DiagnosticService.service_code.ilike(term),
                    Partner.display_name.ilike(term),
                    PartnerServiceMapping.partner_service_name.ilike(term),
                )
            )

        if province:
            query = query.filter(
                or_(
                    Partner.province.ilike(f"%{province.strip()}%"),
                    Partner.city.ilike(f"%{province.strip()}%"),
                )
            )

        if city:
            query = query.filter(Partner.city.ilike(f"%{city.strip()}%"))

        if district:
            query = query.filter(Partner.district.ilike(f"%{district.strip()}%"))

        if partner_type:
            query = query.filter(Partner.partner_type == partner_type.upper())

        if home_collection is not None:
            flag = str(home_collection).lower() in ("1", "true", "yes")
            query = query.filter(
                PartnerServiceMapping.home_collection_available.is_(flag)
            )

        if max_price is not None:
            try:
                query = query.filter(PartnerServiceMapping.price <= float(max_price))
            except (TypeError, ValueError):
                pass

        rows = query.all()
        partner_ids = {partner.id for _, partner, _ in rows}
        verification_map = {}
        availability_map = {}

        if partner_ids:
            items = PartnerVerificationItem.query.filter(
                PartnerVerificationItem.partner_id.in_(partner_ids)
            ).all()
            for item in items:
                verification_map.setdefault(item.partner_id, []).append(item)

            for partner_id in partner_ids:
                availability_map[partner_id] = PartnerAvailabilityService.get_or_create(
                    partner_id,
                    search_date,
                )

        results = []
        for mapping, partner, service in rows:
            availability = availability_map.get(partner.id)
            ranking = RankingService.score_mapping(
                partner,
                mapping,
                service,
                verification_map.get(partner.id, []),
                availability,
            )
            turnaround_hours = (
                mapping.turnaround_hours
                or service.estimated_turnaround_hours
                or partner.average_result_time_hours
            )
            results.append(
                {
                    "mapping_id": mapping.id,
                    "partner": MarketplaceSearchService._partner_marketplace_dict(partner),
                    "service": service.to_dict(),
                    "price": mapping.price,
                    "currency": mapping.currency,
                    "turnaround_hours": turnaround_hours,
                    "rating": partner.rating or 0.0,
                    "review_count": partner.review_count or 0,
                    "completed_orders": partner.completed_orders or 0,
                    "trust_score": ranking["trust_score"],
                    "recommendation_tags": ranking["recommendation_tags"],
                    "recommendation_reason": ranking["recommendation_reason"],
                    "availability": ranking["availability"],
                    "book_url": f"/marketplace/book?mapping_id={mapping.id}",
                    "home_collection_available": mapping.home_collection_available,
                }
            )

        if sort == "price_asc":
            results.sort(key=lambda item: item["price"])
        elif sort == "price_desc":
            results.sort(key=lambda item: item["price"], reverse=True)
        elif sort == "rating_desc":
            results.sort(
                key=lambda item: (item["rating"], item["review_count"]),
                reverse=True,
            )
        elif sort == "turnaround_asc":
            results.sort(
                key=lambda item: item["turnaround_hours"] or 9999,
            )
        else:
            results.sort(key=lambda item: item["trust_score"], reverse=True)

        return {
            "count": len(results),
            "sort": sort,
            "search_date": search_date,
            "results": results,
        }
