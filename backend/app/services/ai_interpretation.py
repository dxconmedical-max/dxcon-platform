def interpret_result(test_name, value):

    try:
        value = float(value)
    except:
        return {
            "status": "UNKNOWN",
            "message": "Cannot interpret"
        }

    if test_name.upper() == "HBA1C":

        if value < 5.7:
            return {
                "status": "NORMAL",
                "message": "Normal glucose metabolism"
            }

        elif value < 6.5:
            return {
                "status": "WARNING",
                "message": "Prediabetes range"
            }

        else:
            return {
                "status": "ABNORMAL",
                "message": "Diabetes range"
            }

    if test_name.upper() == "GLUCOSE":

        if value < 100:
            return {
                "status": "NORMAL",
                "message": "Normal fasting glucose"
            }

        elif value < 126:
            return {
                "status": "WARNING",
                "message": "Prediabetes range"
            }

        else:
            return {
                "status": "ABNORMAL",
                "message": "Diabetes range"
            }

    return {
        "status": "UNKNOWN",
        "message": "Rule not found"
    }
