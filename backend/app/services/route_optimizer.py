import math


def to_float(value):
    try:
        return float(value)
    except:
        return None


def haversine_km(lat1, lon1, lat2, lon2):

    lat1 = to_float(lat1)
    lon1 = to_float(lon1)
    lat2 = to_float(lat2)
    lon2 = to_float(lon2)

    if None in [lat1, lon1, lat2, lon2]:
        return 0

    r = 6371

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(d_lambda / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return r * c


def calculate_route_distance(points):

    if len(points) < 2:
        return 0

    total = 0

    for i in range(len(points) - 1):
        total += haversine_km(
            points[i][0],
            points[i][1],
            points[i + 1][0],
            points[i + 1][1]
        )

    return round(total, 2)


def estimate_minutes(distance_km, average_speed_kmh=22):

    if not distance_km:
        return 0

    return int((distance_km / average_speed_kmh) * 60)
