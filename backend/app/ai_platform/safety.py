CLINICAL_DISCLAIMER = (
    "This output is advisory only and does not constitute a medical diagnosis. "
    "Human clinical review is required before any clinical action."
)

BLOCKED_PATTERNS = (
    "definitive diagnosis",
    "auto-diagnose",
    "automatic diagnosis",
    "diagnose without review",
    "replace physician",
    "prescribe without review",
)


class AISafetyPolicy:
    @staticmethod
    def check_request(task_type: str, input_data: dict) -> dict:
        text = " ".join(str(value) for value in (input_data or {}).values()).lower()
        violations = [pattern for pattern in BLOCKED_PATTERNS if pattern in text]
        if violations:
            return {
                "allowed": False,
                "violations": violations,
                "message": "Request blocked by AI safety policy. Automated diagnosis is not permitted.",
            }
        return {"allowed": True, "violations": [], "human_review_required": True}

    @staticmethod
    def wrap_output(output: dict, task_type: str = "general") -> dict:
        wrapped = dict(output or {})
        wrapped["advisory_only"] = True
        wrapped["human_review_required"] = True
        wrapped["clinical_disclaimer"] = CLINICAL_DISCLAIMER
        wrapped["task_type"] = task_type
        wrapped["automation_level"] = "advisory"
        return wrapped

    @staticmethod
    def enforce_disclaimer(response: dict) -> dict:
        if "clinical_disclaimer" not in response:
            response["clinical_disclaimer"] = CLINICAL_DISCLAIMER
        response["human_review_required"] = True
        response["advisory_only"] = True
        return response
