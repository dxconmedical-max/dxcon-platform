def analyze_profile(results):

    findings = []
    recommendations = []
    risk_score = 0

    for result in results:

        name = (result.test_name or "").lower()

        try:
            value = float(result.result_value)
        except:
            continue

        if "hba1c" in name and value >= 6.5:
            findings.append("Type 2 Diabetes Risk")
            recommendations.append(
                "Endocrinology consultation"
            )
            risk_score += 3

        if "glucose" in name and value >= 126:
            findings.append("Hyperglycemia")
            recommendations.append(
                "Repeat fasting glucose"
            )
            risk_score += 2

        if "triglyceride" in name and value >= 150:
            findings.append("Metabolic Syndrome Risk")
            recommendations.append(
                "Lipid profile follow-up"
            )
            risk_score += 2

        if "cholesterol" in name and value >= 200:
            findings.append("Cardiovascular Risk")
            recommendations.append(
                "Cardiology assessment"
            )
            risk_score += 1

    if risk_score >= 5:
        level = "HIGH"
    elif risk_score >= 3:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "risk_level": level,
        "risk_score": risk_score,
        "findings": list(set(findings)),
        "recommendations": list(set(recommendations))
    }
