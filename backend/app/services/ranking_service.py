from app.core.statuses import (
    PARTNER_ACTIVE,
    PARTNER_APPROVED,
    RECOMMENDATION_TAG_DXCON_VERIFIED,
    RECOMMENDATION_TAG_FAST_RESULT,
    RECOMMENDATION_TAG_HOME_COLLECTION,
    RECOMMENDATION_TAG_LABELS,
    RECOMMENDATION_TAG_LOW_PRICE,
    RECOMMENDATION_TAG_TOP_RATED,
    VERIFICATION_VERIFIED,
)
from app.services.partner_availability import PartnerAvailabilityService


class RankingService:

    MAX_PRICE_REFERENCE = 500000.0
    MAX_TURNAROUND_REFERENCE = 72.0
    LOW_PRICE_THRESHOLD = 150000.0

    @staticmethod
    def verification_ratio(verification_items):
        if not verification_items:
            return 0.0

        verified = sum(
            1 for item in verification_items if item.status == VERIFICATION_VERIFIED
        )
        return verified / len(verification_items)

    @staticmethod
    def partner_status_score(partner_status):
        if partner_status == PARTNER_ACTIVE:
            return 10.0
        if partner_status == PARTNER_APPROVED:
            return 7.0
        return 0.0

    @staticmethod
    def build_recommendation_tags(
        partner,
        mapping,
        diagnostic_service,
        verification_items=None,
    ):
        verification_items = verification_items or []
        tags = []

        if RankingService.verification_ratio(verification_items) >= 0.8:
            tags.append(RECOMMENDATION_TAG_DXCON_VERIFIED)

        turnaround_hours = (
            mapping.turnaround_hours
            or diagnostic_service.estimated_turnaround_hours
            or partner.average_result_time_hours
            or 24.0
        )
        if turnaround_hours <= 24:
            tags.append(RECOMMENDATION_TAG_FAST_RESULT)

        if (mapping.price or 0.0) <= RankingService.LOW_PRICE_THRESHOLD:
            tags.append(RECOMMENDATION_TAG_LOW_PRICE)

        if mapping.home_collection_available:
            tags.append(RECOMMENDATION_TAG_HOME_COLLECTION)

        if (partner.rating or 0.0) >= 4.0:
            tags.append(RECOMMENDATION_TAG_TOP_RATED)

        return tags

    @staticmethod
    def recommendation_reason_from_tags(tags):
        if not tags:
            return "Available in your area"

        labels = [RECOMMENDATION_TAG_LABELS.get(tag, tag.replace("_", " ").title()) for tag in tags]
        return ", ".join(labels[:3])

    @staticmethod
    def score_mapping(
        partner,
        mapping,
        diagnostic_service,
        verification_items=None,
        availability=None,
    ):
        verification_items = verification_items or []
        rating = partner.rating or 0.0
        completed_orders = partner.completed_orders or 0
        price = mapping.price or 0.0
        turnaround_hours = (
            mapping.turnaround_hours
            or diagnostic_service.estimated_turnaround_hours
            or partner.average_result_time_hours
            or 24.0
        )

        rating_score = min(max(rating, 0.0), 5.0) / 5.0 * 25.0
        volume_score = min(completed_orders / 1000.0, 1.0) * 20.0
        price_score = max(0.0, 15.0 - (price / RankingService.MAX_PRICE_REFERENCE) * 15.0)
        turnaround_score = max(
            0.0,
            15.0 - (turnaround_hours / RankingService.MAX_TURNAROUND_REFERENCE) * 15.0,
        )
        home_score = 10.0 if mapping.home_collection_available else 0.0
        status_score = RankingService.partner_status_score(partner.status)
        verification_score = RankingService.verification_ratio(verification_items) * 5.0
        capacity_penalty = PartnerAvailabilityService.ranking_penalty(availability)

        trust_score = round(
            rating_score
            + volume_score
            + price_score
            + turnaround_score
            + home_score
            + status_score
            + verification_score
            - capacity_penalty,
            2,
        )

        recommendation_tags = RankingService.build_recommendation_tags(
            partner,
            mapping,
            diagnostic_service,
            verification_items,
        )

        return {
            "trust_score": max(trust_score, 0.0),
            "recommendation_tags": recommendation_tags,
            "recommendation_reason": RankingService.recommendation_reason_from_tags(
                recommendation_tags
            ),
            "availability": availability.to_dict() if availability else None,
            "capacity_penalty": capacity_penalty,
            "breakdown": {
                "rating_score": round(rating_score, 2),
                "volume_score": round(volume_score, 2),
                "price_score": round(price_score, 2),
                "turnaround_score": round(turnaround_score, 2),
                "home_collection_score": round(home_score, 2),
                "partner_status_score": round(status_score, 2),
                "verification_score": round(verification_score, 2),
                "capacity_penalty": capacity_penalty,
            },
        }
