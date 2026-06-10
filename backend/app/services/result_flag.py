def calculate_result_flag(result_value, reference_range):

    try:
        value = float(result_value)
    except:
        return "UNKNOWN"

    if not reference_range:
        return "UNKNOWN"

    ref = reference_range.replace(" ", "")

    try:
        if "-" in ref:
            low, high = ref.split("-")
            low = float(low)
            high = float(high)

            if value < low:
                return "LOW"

            if value > high:
                return "HIGH"

            return "NORMAL"

        if ref.startswith("<"):
            high = float(ref.replace("<", ""))

            if value >= high:
                return "HIGH"

            return "NORMAL"

        if ref.startswith(">"):
            low = float(ref.replace(">", ""))

            if value <= low:
                return "LOW"

            return "NORMAL"

    except:
        return "UNKNOWN"

    return "UNKNOWN"
