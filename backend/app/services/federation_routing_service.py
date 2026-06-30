import json
import math
import uuid

from app.core.statuses import FEDERATION_LAB_ONLINE
from app.extensions.db import db
from app.models.federation_core import FederatedLab
from app.models.federation_routing import RoutingAudit, RoutingDecision, RoutingRule
from app.services.federation_capacity_service import CapacityCalculatorService
from app.services.federation_service import FederationCapabilityService, FederationError


class RoutingScoreService:

    DEFAULT_WEIGHTS = {
        "distance": 0.15,
        "capacity": 0.15,
        "sla": 0.15,
        "contract": 0.1,
        "price": 0.1,
        "capability": 0.15,
        "priority": 0.1,
        "online": 0.1,
    }

    @staticmethod
    def _distance_score(lab, origin_lat, origin_lng):
        if origin_lat is None or origin_lng is None or lab.latitude is None or lab.longitude is None:
            return 0.7
        distance_km = math.sqrt(
            (lab.latitude - origin_lat) ** 2 + (lab.longitude - origin_lng) ** 2
        ) * 111
        return max(0, 1 - min(distance_km / 100, 1))

    @staticmethod
    def score_lab(lab, request, weights=None):
        weights = weights or RoutingScoreService.DEFAULT_WEIGHTS
        origin_lat = request.get("origin_latitude")
        origin_lng = request.get("origin_longitude")
        test_code = request.get("test_code")

        capacity = CapacityCalculatorService.calculate_for_lab(lab.id)
        capacity_score = min(capacity["remaining_capacity"] / max(capacity["total_capacity"], 1), 1)
        sla_score = min(lab.sla_minutes / 480, 1) if lab.sla_minutes else 0.5
        contract_score = 1.0 if lab.contract_active else 0.0
        price_score = max(0, 1 - (lab.base_price or 0) / 500000)
        capability_score = (
            1.0 if FederationCapabilityService.lab_supports_test(lab.id, test_code) else 0.0
        )
        priority_score = min((lab.priority or 50) / 100, 1)
        online_score = 1.0 if lab.status == FEDERATION_LAB_ONLINE else 0.0
        distance_score = RoutingScoreService._distance_score(lab, origin_lat, origin_lng)

        breakdown = {
            "distance": round(distance_score * weights["distance"], 4),
            "capacity": round(capacity_score * weights["capacity"], 4),
            "sla": round(sla_score * weights["sla"], 4),
            "contract": round(contract_score * weights["contract"], 4),
            "price": round(price_score * weights["price"], 4),
            "capability": round(capability_score * weights["capability"], 4),
            "priority": round(priority_score * weights["priority"], 4),
            "online": round(online_score * weights["online"], 4),
        }
        total = round(sum(breakdown.values()), 4)
        return {
            "lab_id": lab.id,
            "lab_code": lab.lab_code,
            "name": lab.name,
            "score_total": total,
            "score_breakdown": breakdown,
            "capacity": capacity,
        }


class SmartRoutingService:

    @staticmethod
    def _active_weights():
        rule = RoutingRule.query.filter_by(is_active=True).first()
        if not rule:
            return RoutingScoreService.DEFAULT_WEIGHTS
        return {
            "distance": rule.weight_distance,
            "capacity": rule.weight_capacity,
            "sla": rule.weight_sla,
            "contract": rule.weight_contract,
            "price": rule.weight_price,
            "capability": rule.weight_capability,
            "priority": rule.weight_priority,
            "online": rule.weight_online,
        }

    @staticmethod
    def route(request, actor_email="SYSTEM"):
        test_code = request.get("test_code")
        candidates = FederatedLab.query.all()
        if test_code:
            candidates = [
                lab
                for lab in candidates
                if FederationCapabilityService.lab_supports_test(lab.id, test_code)
            ]
        if not candidates:
            raise FederationError("No candidate labs available for routing", 404)

        weights = SmartRoutingService._active_weights()
        scored = [
            RoutingScoreService.score_lab(lab, request, weights)
            for lab in candidates
            if lab.status == FEDERATION_LAB_ONLINE or request.get("include_offline")
        ]
        if not scored:
            raise FederationError("No online labs available for routing", 409)

        scored.sort(key=lambda row: row["score_total"], reverse=True)
        best = scored[0]
        decision = RoutingDecision(
            decision_code=f"RTE-{uuid.uuid4().hex[:10].upper()}",
            request_ref=request.get("request_ref"),
            selected_lab_id=best["lab_id"],
            test_code=test_code,
            score_total=best["score_total"],
            score_breakdown_json=json.dumps(best["score_breakdown"]),
            candidate_count=len(scored),
        )
        db.session.add(decision)
        db.session.flush()
        audit = RoutingAudit(
            audit_code=f"RAU-{uuid.uuid4().hex[:10].upper()}",
            routing_decision_id=decision.id,
            action="ROUTE_SELECTED",
            actor_email=actor_email,
            details_json=json.dumps({"top_candidates": scored[:5]}),
        )
        db.session.add(audit)
        db.session.commit()
        return {
            "decision": decision.to_dict(),
            "selected_lab": best,
            "candidates": scored[:10],
        }

    @staticmethod
    def list_decisions(page=1, page_size=50):
        total = RoutingDecision.query.count()
        rows = (
            RoutingDecision.query.order_by(RoutingDecision.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "decisions": [row.to_dict() for row in rows],
        }

    @staticmethod
    def list_audit(page=1, page_size=50):
        total = RoutingAudit.query.count()
        rows = (
            RoutingAudit.query.order_by(RoutingAudit.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "audits": [row.to_dict() for row in rows],
        }
