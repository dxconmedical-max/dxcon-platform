def generate_medical_summary(results):

    findings = []

    for result in results:

        name = (result.test_name or "").lower()

        try:
            value = float(result.result_value)
        except:
            continue

        if "hba1c" in name and value >= 6.5:
            findings.append("HbA1c tang")

        if "glucose" in name and value >= 126:
            findings.append("Duong huyet tang")

        if "triglyceride" in name and value >= 150:
            findings.append("Triglyceride tang")

        if "cholesterol" in name and value >= 200:
            findings.append("Cholesterol tang")

    if len(findings) >= 2:
        return (
            "Multiple metabolic markers are abnormal. "
            "Risk of metabolic syndrome or diabetes may be increased. "
            "Recommend endocrinology consultation."
        )

    if len(findings) == 1:
        return (
            findings[0]
            + ". Further monitoring and clinical correlation are recommended."
        )

    return (
        "No major abnormal pattern detected from available test results."
    )
