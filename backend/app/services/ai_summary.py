def build_summary(results):

    risk = "LOW"
    findings = []
    recommendations = []

    abnormal_results = [
        r for r in results
        if r.flag and r.flag != "NORMAL"
    ]

    if abnormal_results:
        risk = "MEDIUM"

        for result in abnormal_results:
            findings.append(
                f"{result.test_name}: {result.result_value} {result.unit or ''} flagged as {result.flag}"
            )

        recommendations.append("Clinical follow-up is recommended.")
        recommendations.append("Doctor review and correlation with symptoms are advised.")
    else:
        findings.append("No significant abnormal laboratory pattern detected.")
        recommendations.append("Continue routine monitoring.")

    return {
        "risk_level": risk,
        "findings": "\\n".join(findings),
        "recommendations": "\\n".join(recommendations)
    }
