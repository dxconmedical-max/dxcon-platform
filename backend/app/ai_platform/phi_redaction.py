import re


EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b")
MRN_PATTERN = re.compile(r"\b(?:MRN|Patient ID|PatientID)[:\s#-]*([A-Za-z0-9-]+)\b", re.IGNORECASE)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact_phi(text: str) -> str:
    if not text:
        return text
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)
    redacted = MRN_PATTERN.sub("[REDACTED_MRN]", redacted)
    redacted = SSN_PATTERN.sub("[REDACTED_SSN]", redacted)
    return redacted


def redact_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return payload
    return {key: redact_phi(str(value)) if isinstance(value, str) else value for key, value in payload.items()}
