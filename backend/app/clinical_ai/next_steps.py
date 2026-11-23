"""Rule-based advisory summary + follow-up suggestions for a lab order.

Deterministic knowledge table (no LLM, no network). Output is a *reference note
for the doctor*: it never states a diagnosis and always requires physician review.
Directions come from the result flag (low/high/critical_*), never from guessing.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

DISCLAIMER = (
    "Ghi chú chỉ mang tính tham khảo, do hệ thống tự động tạo theo quy tắc, "
    "không phải chẩn đoán. Bác sĩ phải xem xét kết quả và bối cảnh lâm sàng "
    "trước khi quyết định."
)

# Each rule: keywords (accent-free, lowercase) -> per direction: considerations + next tests.
RULES: list[dict[str, Any]] = [
    {"key": "glucose", "label": "Glucose", "kw": ["glucose", "duong huyet", "glu"],
     "high": ("Tăng đường huyết: cần loại trừ rối loạn dung nạp glucose hoặc đái tháo đường (lúc đói/ngẫu nhiên, ăn gần xét nghiệm).",
              ["HbA1c", "Glucose lúc đói (lặp lại)", "Nghiệm pháp dung nạp glucose 75g", "Nước tiểu 10 thông số (đường, ceton)"]),
     "low": ("Hạ đường huyết: cần đối chiếu triệu chứng, thời gian nhịn ăn, thuốc đang dùng.",
             ["Glucose lặp lại", "Insulin, C-peptid (theo chỉ định bác sĩ)"])},
    {"key": "hba1c", "label": "HbA1c", "kw": ["hba1c", "a1c"],
     "high": ("HbA1c tăng: phản ánh đường huyết trung bình 2–3 tháng, cần đối chiếu tiêu chuẩn đái tháo đường.",
              ["Glucose lúc đói", "Lipid máu", "Creatinin/eGFR", "Microalbumin niệu"]), "low": None},
    {"key": "ferritin", "label": "Ferritin", "kw": ["ferritin"],
     "low": ("Ferritin thấp: gợi ý thiếu sắt dự trữ.",
             ["Công thức máu (Hb, MCV, MCH)", "Sắt huyết thanh, TIBC, độ bão hòa transferrin", "Tìm nguyên nhân mất máu/hấp thu kém nếu cần"]),
     "high": ("Ferritin tăng: có thể do quá tải sắt hoặc viêm/bệnh gan (ferritin là protein phản ứng pha cấp).",
              ["CRP", "Sắt, độ bão hòa transferrin", "AST/ALT"])},
    {"key": "hemoglobin", "label": "Hemoglobin", "kw": ["hemoglobin", "hgb", "hb "],
     "low": ("Hemoglobin thấp: gợi ý thiếu máu, cần phân loại theo MCV.",
             ["Ferritin, sắt, TIBC", "Vitamin B12, folate", "Hồng cầu lưới", "Phết máu ngoại vi"]),
     "high": ("Hemoglobin tăng: cần loại trừ mất nước hoặc đa hồng cầu.", ["Công thức máu lặp lại", "Erythropoietin (theo chỉ định)"])},
    {"key": "wbc", "label": "Bạch cầu", "kw": ["wbc", "bach cau"],
     "high": ("Bạch cầu tăng: có thể gặp trong nhiễm trùng, viêm hoặc nguyên nhân khác.",
              ["Công thức bạch cầu", "CRP/Procalcitonin", "Phết máu ngoại vi"]),
     "low": ("Bạch cầu giảm: cần đối chiếu thuốc, nhiễm virus và các nguyên nhân khác.", ["Công thức bạch cầu", "Phết máu ngoại vi", "Lặp lại công thức máu"])},
    {"key": "platelet", "label": "Tiểu cầu", "kw": ["plt", "tieu cau", "platelet"],
     "low": ("Tiểu cầu giảm: cần loại trừ tiểu cầu giả do kết cụm.", ["Phết máu ngoại vi", "Lặp lại mẫu chống đông citrat", "Đông máu cơ bản"]),
     "high": ("Tiểu cầu tăng: có thể phản ứng (viêm, thiếu sắt) hoặc nguyên phát.", ["Ferritin", "CRP"])},
    {"key": "alt_ast", "label": "ALT/AST", "kw": ["alt", "sgpt", "ast", "sgot"],
     "high": ("Men gan tăng: gợi ý tổn thương tế bào gan (viêm gan, mỡ gan, thuốc, rượu…).",
              ["AST/ALT lặp lại", "GGT, ALP, bilirubin", "HBsAg, Anti-HCV", "Siêu âm gan"]), "low": None},
    {"key": "creatinine", "label": "Creatinin", "kw": ["creatinin", "creatinine"],
     "high": ("Creatinin tăng: cần đánh giá chức năng thận (eGFR) và loại trừ nguyên nhân trước thận.",
              ["eGFR", "Ure", "Nước tiểu 10 thông số, tỉ lệ albumin/creatinin niệu", "Điện giải đồ"]), "low": None},
    {"key": "urea", "label": "Ure", "kw": ["urea", "ure ", "bun"],
     "high": ("Ure tăng: có thể do giảm chức năng thận, mất nước hoặc chế độ ăn.", ["Creatinin/eGFR", "Điện giải đồ"]), "low": None},
    {"key": "uric", "label": "Acid uric", "kw": ["uric"],
     "high": ("Acid uric tăng: nguy cơ gút/sỏi thận, cần đối chiếu triệu chứng.", ["Creatinin/eGFR", "Nước tiểu 10 thông số", "Lipid máu"]), "low": None},
    {"key": "cholesterol", "label": "Mỡ máu", "kw": ["cholesterol", "ldl", "triglycerid", "tg"],
     "high": ("Rối loạn mỡ máu: là yếu tố nguy cơ tim mạch.", ["Bộ mỡ máu đầy đủ lúc đói", "Glucose/HbA1c", "TSH", "AST/ALT"]), "low": None},
    {"key": "tsh", "label": "TSH", "kw": ["tsh"],
     "high": ("TSH tăng: gợi ý suy giáp (nguyên phát hoặc dưới lâm sàng).", ["FT4", "Anti-TPO"]),
     "low": ("TSH giảm: gợi ý cường giáp hoặc đang dùng hormon giáp.", ["FT4, FT3", "Anti-TSH receptor (TRAb)"])},
    {"key": "crp", "label": "CRP", "kw": ["crp"],
     "high": ("CRP tăng: dấu hiệu viêm/nhiễm trùng, không đặc hiệu.", ["Công thức máu", "Procalcitonin (nếu nghi nhiễm khuẩn)", "Cấy máu/nước tiểu theo lâm sàng"]), "low": None},
    {"key": "potassium", "label": "Kali", "kw": ["potassium", "kali", "k+"],
     "high": ("Kali tăng: cần loại trừ tán huyết mẫu và đánh giá nguy cơ rối loạn nhịp.", ["Lặp lại mẫu mới", "Creatinin/eGFR", "Điện tâm đồ"]),
     "low": ("Kali giảm: đối chiếu thuốc lợi tiểu, nôn/tiêu chảy.", ["Điện giải đồ, magie", "Điện tâm đồ"])},
    {"key": "sodium", "label": "Natri", "kw": ["sodium", "natri", "na+"],
     "high": ("Natri tăng: thường do mất nước.", ["Điện giải đồ lặp lại", "Creatinin"]),
     "low": ("Natri giảm: cần đánh giá thể tích dịch và thuốc.", ["Điện giải đồ lặp lại", "Áp lực thẩm thấu máu/niệu"])},
    {"key": "vitd", "label": "Vitamin D", "kw": ["vitamin d", "25-oh", "25 oh"],
     "low": ("Vitamin D thấp: nguy cơ loãng xương, yếu cơ.", ["Canxi, phospho, PTH"]), "high": None},
]


def _norm(text: str | None) -> str:
    t = unicodedata.normalize("NFD", str(text or "")).lower()
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"\s+", " ", t).strip() + " "


def _direction(flag: str | None) -> str | None:
    f = str(flag or "").lower()
    if f.endswith("high") or f in ("h", "hh"):
        return "high"
    if f.endswith("low") or f in ("l", "ll"):
        return "low"
    return None


def _match(item: dict[str, Any]) -> dict[str, Any] | None:
    hay = _norm(f"{item.get('test_name') or ''} {item.get('test_code') or ''}")
    for rule in RULES:
        for kw in rule["kw"]:
            if kw.strip() and re.search(rf"(^|[^a-z0-9]){re.escape(kw.strip())}([^a-z0-9]|$)", hay):
                return rule
    return None


def build_next_steps(items: list[dict[str, Any]]) -> dict[str, Any]:
    abnormal, notes, tests = [], [], []
    seen_tests: set[str] = set()
    critical = []
    unmatched = []
    for it in items:
        flag = str(it.get("flag") or "").lower()
        direction = _direction(flag)
        if direction is None:
            continue
        row = {
            "test_name": it.get("test_name"), "result_value": it.get("result_value"),
            "unit": it.get("unit"), "reference_range": it.get("reference_range"), "flag": flag,
        }
        abnormal.append(row)
        if flag.startswith("critical"):
            critical.append(row)
        rule = _match(it)
        spec = rule.get(direction) if rule else None
        if not spec:
            unmatched.append(str(it.get("test_name")))
            continue
        notes.append({"test_name": it.get("test_name"), "direction": direction, "consideration": spec[0]})
        for t in spec[1]:
            if t not in seen_tests:
                seen_tests.add(t)
                tests.append({"test": t, "because": it.get("test_name")})
    if abnormal:
        summary = f"Có {len(abnormal)} chỉ số ngoài khoảng tham chiếu trên tổng {len(items)} chỉ số."
        if critical:
            summary += f" {len(critical)} chỉ số ở mức nguy kịch, cần báo bác sĩ điều trị ngay."
    else:
        summary = f"Tất cả {len(items)} chỉ số nằm trong khoảng tham chiếu hoặc chưa có cờ bất thường."
    return {
        "summary": summary,
        "abnormal": abnormal,
        "critical": critical,
        "considerations": notes,
        "suggested_tests": tests,
        "no_rule_for": unmatched,
        "advisory_only": True,
        "doctor_review_required": True,
        "diagnosis_automation": False,
        "disclaimer": DISCLAIMER,
    }
