import math
import airportsdata


AIRPORTS = airportsdata.load()


def haversine_km(lat1, lon1, lat2, lon2):

    R = 6371

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = lat2 - lat1
    dlon = math.radians(lon2) - math.radians(lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return R * 2 * math.asin(math.sqrt(a))


def find_nearest_airport(latitude, longitude):

    if latitude is None or longitude is None:
        return None

    best_airport = None
    best_distance = None

    for airport in AIRPORTS.values():

        if not airport.get("iata"):
            continue

        try:
            airport_lat = float(airport["lat"])
            airport_lon = float(airport["lon"])
        except (KeyError, TypeError, ValueError):
            continue

        distance = haversine_km(
            float(latitude),
            float(longitude),
            airport_lat,
            airport_lon
        )

        if best_distance is None or distance < best_distance:

            best_distance = distance
            best_airport = airport

    if best_airport is None:
        return None

    return {
        "name": best_airport.get("name", ""),
        "iata": best_airport.get("iata", ""),
        "icao": best_airport.get("icao", ""),
        "city": best_airport.get("city", ""),
        "country": best_airport.get("country", ""),
        "latitude": best_airport.get("lat"),
        "longitude": best_airport.get("lon"),
        "distance_km": round(best_distance, 2)
    }