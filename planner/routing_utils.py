import json
import urllib.request
import urllib.error
import math


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Calculate the approximate straight-line (great-circle) distance in km
    between two coordinates using the Haversine formula.
    Used as an offline fallback when routing services are unavailable.
    """
    R = 6371  # Earth radius in kilometers

    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def get_road_routing(start_lat, start_lon, end_lat, end_lon):
    """
    Fetch real road distance (km) and driving travel time (minutes) between
    two coordinates anywhere in the world using Open Source Routing Machine (OSRM).

    OSRM is free and does not require an API key.

    Returns:
        dict: {
            "distance_km": float,        # Actual driving distance in km
            "duration_minutes": int,     # Estimated driving time in minutes
            "is_road_distance": bool     # True if real road routing succeeded
        }
    """
    if start_lat is None or start_lon is None or end_lat is None or end_lon is None:
        return None

    try:
        # Note: OSRM expects coordinates in {longitude},{latitude} order
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{start_lon},{start_lat};{end_lon},{end_lat}?overview=false"
        )

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BusinessTravelPlannerMiniProject/1.0"}
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            # distance is in meters -> convert to kilometers
            distance_km = round(route["distance"] / 1000.0, 2)
            # duration is in seconds -> convert to minutes
            duration_minutes = max(1, round(route["duration"] / 60.0))

            return {
                "distance_km": distance_km,
                "duration_minutes": duration_minutes,
                "is_road_distance": True
            }

    except Exception:
        # If network or OSRM is temporarily unavailable, fall back safely
        pass

    # Fallback: estimate road distance as straight-line * 1.3, average speed 40 km/h
    straight_dist = haversine_km(start_lat, start_lon, end_lat, end_lon)
    fallback_km = round(straight_dist * 1.3, 2)
    fallback_minutes = max(1, round((fallback_km / 40.0) * 60))

    return {
        "distance_km": fallback_km,
        "duration_minutes": fallback_minutes,
        "is_road_distance": False
    }
