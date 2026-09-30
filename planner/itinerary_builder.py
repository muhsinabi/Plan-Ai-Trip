from datetime import datetime, timedelta
import math
from .airport_utils import find_nearest_airport, haversine_km
from .routing_utils import get_road_routing


# Common major airline prefixes for realistic flight numbers
AIRLINE_PREFIXES = {
    "SIN": "SQ",   # Singapore Airlines
    "DXB": "EK",   # Emirates
    "RUH": "SV",   # Saudia
    "DOH": "QR",   # Qatar Airways
    "MCT": "WY",   # Oman Air
    "LHR": "BA",   # British Airways
    "JFK": "AA",   # American Airlines
    "CCJ": "AI",   # Air India
    "COK": "IX",   # Air India Express
}


def get_flight_info(origin_iata, dest_iata, dist_km):
    """
    Generate realistic flight code and duration based on route distance.
    """
    prefix = AIRLINE_PREFIXES.get(origin_iata, "FL")
    flight_num = f"{prefix} {abs(hash(f'{origin_iata}-{dest_iata}')) % 800 + 100}"

    # Approximate flight time: ~700 km/h cruising + 30 min takeoff/landing
    hours = max(1.0, (dist_km / 700.0) + 0.5)
    hours_int = int(hours)
    minutes_int = int((hours - hours_int) * 60)
    minutes_int = (minutes_int // 5) * 5  # round to nearest 5 min

    if minutes_int == 0:
        duration_str = f"{hours_int} hrs"
    else:
        duration_str = f"{hours_int}h {minutes_int:02d}m"

    return {
        "flight_code": flight_num,
        "duration_str": duration_str,
        "duration_minutes": int(hours * 60)
    }


def parse_time_str(time_str):
    """Parse time string like '09:00 AM' or '14:30' into datetime.time object."""
    if not time_str:
        return datetime.strptime("09:00", "%H:%M").time()
    for fmt in ("%I:%M %p", "%H:%M", "%I:%M%p"):
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            pass
    return datetime.strptime("09:00", "%H:%M").time()


def format_display_date(date_str):
    """Format '2026-12-12' into 'Fri, 12 Dec 2026'."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%a, %d %b %Y")
    except Exception:
        return date_str
def normalize_event(event):
    """Make backend event data compatible with planner.js."""

    title = event.get("title", "")
    transport = event.get("transport", "")

    # Event type used by planner.js
    if "flight" in title.lower() or transport.lower() == "flight":
        event_type = "flight"
    elif "meeting" in title.lower():
        event_type = "meeting"
    elif "hotel" in title.lower() or "check-in" in title.lower():
        event_type = "hotel"
    elif "airport" in title.lower():
        event_type = "airport"
    elif "rest" in title.lower():
        event_type = "rest"
    elif "home" in title.lower():
        event_type = "home"
    else:
        event_type = "transport"

    # Convert "35 km" / "12 km" into a number
    distance_text = str(event.get("distance", ""))
    distance_km = None

    try:
        distance_km = float(
            distance_text.replace("km", "").strip()
        )
    except (ValueError, AttributeError):
        pass

    # Convert "30 min" into a number
    duration_text = str(event.get("duration", ""))
    travel_minutes = None

    try:
        if "h" in duration_text.lower():
            hours = 0
            minutes = 0

            parts = duration_text.lower().replace(" ", "").split("h")

            if parts[0]:
                hours = int(parts[0])

            if len(parts) > 1:
                minutes = int(
                    parts[1].replace("m", "") or 0
                )

            travel_minutes = hours * 60 + minutes

        else:
            travel_minutes = int(
                duration_text.lower()
                .replace("min", "")
                .strip()
            )

    except (ValueError, AttributeError):
        pass

    event["type"] = event_type
    event["distance_km"] = distance_km
    event["travel_minutes"] = travel_minutes
    event["transport_mode"] = transport
    event["maps_url"] = event.get("link", "")
    event["location"] = event.get(
        "location_col",
        event.get("description", "")
    )

    # Used by the JavaScript for overnight display
    event["sleepover"] = (
        "sleepover: yes" in str(
            event.get("booking_details", "")
        ).lower()
    )

    return event


def build_complete_itinerary(participant, meetings_data):
    """
    Builds the complete business travel itinerary for a participant:
    - Day 1: Leave home -> Airport -> Flight -> Arrival -> Hotel Check-in -> Overnight
    - Meeting Days: Hotel -> Meeting -> Return to Hotel -> Rest -> Overnight
    - Inter-city travel: Hotel -> Airport -> Flight -> Hotel Check-in -> Overnight
    - Final Day: Return to Airport -> Return Flight -> Arrive at home/origin
    """
    days = []
    export_rows = []  # For PDF & Excel table export

    # Participant origin & departure airport
    origin_name = participant.current_location
    dept_airport_str = participant.departure_airport or ""
    dept_iata = "DEP"
    if "(" in dept_airport_str and ")" in dept_airport_str:
        dept_iata = dept_airport_str.split("(")[-1].replace(")", "").strip()

    airport_dist_km = float(participant.airport_distance_km or 25.0)
    airport_drive_mins = int(participant.airport_travel_minutes or 35)

    if not meetings_data:
        return {
            "days": [],
            "export_rows": [],
            "route_summary": origin_name,
            "total_flights": 0,
            "hotel_nights": 0,
            "total_cost_sar": "SAR 0"
        }

    # Sort meetings by date and time
    sorted_meetings = sorted(
        meetings_data,
        key=lambda m: (m.get("date", ""), m.get("time", ""))
    )

    # Route summary (e.g. Singapore (SIN) -> Riyadh -> Doha -> Singapore (SIN))
    route_cities = [f"{origin_name} ({dept_iata})" if dept_iata != "DEP" else origin_name]
    for m in sorted_meetings:
        loc = m.get("location", "Meeting")
        city = loc.split(",")[0].strip()
        if city not in route_cities:
            route_cities.append(city)
    route_cities.append(f"{origin_name} ({dept_iata})" if dept_iata != "DEP" else origin_name)
    route_summary = " → ".join(route_cities)

    total_flights = 0
    total_hotel_nights = 0

    # Process each meeting in chronological sequence
    prev_meeting = None
    prev_hotel = None
    prev_dest_iata = dept_iata

    day_counter = 1

    for idx, meeting in enumerate(sorted_meetings):
        meet_loc = meeting.get("location", "Business Meeting")
        meet_city = meet_loc.split(",")[0].strip()
        meet_date_str = meeting.get("date")
        meet_time_str = meeting.get("time", "09:00 AM")
        hotel_name = meeting.get("hotel_name") or f"Hilton {meet_city}"
        hotel_addr = f"{hotel_name}, {meet_city}"
        sleepover = meeting.get("sleepover", True)

        # Find destination airport for this meeting
        meet_lat = meeting.get("latitude")
        meet_lon = meeting.get("longitude")
        dest_airport = find_nearest_airport(meet_lat, meet_lon) if (meet_lat and meet_lon) else None
        dest_iata = dest_airport["iata"] if dest_airport else "ARR"
        dest_airport_name = dest_airport["name"] if dest_airport else f"{meet_city} Airport"

        meet_time = parse_time_str(meet_time_str)
        meet_time_formatted = meet_time.strftime("%I:%M %p")
        end_time_dt = datetime.combine(datetime.today(), meet_time) + timedelta(minutes=120)
        meet_end_formatted = end_time_dt.strftime("%I:%M %p")

        meeting_date = datetime.strptime(meet_date_str, "%Y-%m-%d")

        # ------------------------------------------------------------------
        # Travel Day to Meeting (Day before meeting, or initial travel)
        # ------------------------------------------------------------------
        if idx == 0:
            travel_date = meeting_date - timedelta(days=1)
            travel_date_str = travel_date.strftime("%Y-%m-%d")
            display_travel_date = travel_date.strftime("%a, %d %b %Y")

            flight_dist = haversine_km(
                float(participant.current_latitude or 0),
                float(participant.current_longitude or 0),
                float(dest_airport["latitude"] if dest_airport else 0),
                float(dest_airport["longitude"] if dest_airport else 0)
            ) if (dest_airport and participant.current_latitude) else 1500.0

            flight_info = get_flight_info(dept_iata, dest_iata, flight_dist)
            total_flights += 1

            # Departure calculations (Leave home 2h buffer before flight)
            flight_dep_time = "06:30 PM"
            flight_dep_dt = datetime.strptime(flight_dep_time, "%I:%M %p")
            leave_home_dt = flight_dep_dt - timedelta(minutes=(airport_drive_mins + 90))
            leave_home_str = leave_home_dt.strftime("%I:%M %p")

            flight_arr_dt = flight_dep_dt + timedelta(minutes=flight_info["duration_minutes"])
            flight_arr_str = flight_arr_dt.strftime("%I:%M %p")
            taxi_arr_dt = flight_arr_dt + timedelta(minutes=30)
            taxi_arr_str = taxi_arr_dt.strftime("%I:%M %p")
            checkin_dt = taxi_arr_dt + timedelta(minutes=30)
            checkin_str = checkin_dt.strftime("%I:%M %p")

            # Day 1 Card
            day1_events = [
                {
                    "time": leave_home_str,
                    "icon": "🚗",
                    "title": "Leave home",
                    "description": f"Travel to airport: {airport_drive_mins} mins ({airport_dist_km} km)<br>📍 {origin_name}",
                    "transport": "Car / Taxi",
                    "distance": f"{airport_dist_km} km",
                    "duration": f"{airport_drive_mins} min",
                    "booking_details": "—",
                    "link_text": "View on Map",
                    "link": f"https://www.google.com/maps/search/?api=1&query={origin_name}+to+{dept_iata}+Airport",
                    "activity_col": f"Leave home → {dept_iata} Airport",
                    "location_col": f"{origin_name} → {dept_iata} Airport"
                },
                {
                    "time": flight_dep_time,
                    "icon": "✈️",
                    "title": f"Flight {flight_info['flight_code']}",
                    "description": f"{dept_iata} → {dest_iata}<br>Duration: {flight_info['duration_str']}",
                    "transport": "Flight",
                    "distance": "—",
                    "duration": flight_info["duration_str"],
                    "booking_details": flight_info["flight_code"],
                    "link_text": "View Flight",
                    "link": f"https://www.google.com/travel/flights?q=flights+from+{dept_iata}+to+{dest_iata}",
                    "activity_col": f"Flight: {dept_iata} → {dest_iata}",
                    "location_col": f"{dept_iata} → {dest_iata}"
                },
                {
                    "time": flight_arr_str,
                    "icon": "🛬",
                    "title": f"Arrive at {dest_airport_name} ({dest_iata})",
                    "description": f"Arrived at destination airport ({dest_iata})",
                    "transport": "Airport",
                    "distance": "—",
                    "duration": "—",
                    "booking_details": "—",
                    "link_text": "View on Map",
                    "link": f"https://www.google.com/maps/search/?api=1&query={dest_airport_name}",
                    "activity_col": f"Arrive {dest_iata} Airport → Hotel",
                    "location_col": hotel_name
                },
                {
                    "time": taxi_arr_str,
                    "icon": "🚕",
                    "title": "Airport to Hotel",
                    "description": "Car / Taxi (30 mins, 35 km)",
                    "transport": "Taxi / Car",
                    "distance": "35 km",
                    "duration": "30 min",
                    "booking_details": "—",
                    "link_text": "View on Map",
                    "link": f"https://www.google.com/maps/search/?api=1&query={dest_iata}+Airport+to+{hotel_name}",
                    "activity_col": "Airport to Hotel",
                    "location_col": hotel_name
                },
                {
                    "time": checkin_str,
                    "icon": "🏨",
                    "title": f"Check-in — {hotel_name}",
                    "description": hotel_addr,
                    "transport": "Hotel",
                    "distance": "—",
                    "duration": "—",
                    "booking_details": f"Sleepover: {'Yes' if sleepover else 'No'}",
                    "link_text": "View Hotel",
                    "link": f"https://www.google.com/travel/hotels?q={hotel_name}+{meet_city}",
                    "activity_col": "Check-in & Rest",
                    "location_col": hotel_addr
                }
            ]

            days.append({
                "day_number": day_counter,
                "date": travel_date_str,
                "display_date": display_travel_date,
                "subtitle": f"Travel to {meet_city}",
                "events": day1_events,
                "overnight": f"Overnight stay: {hotel_name} ({travel_date.strftime('%d %b')})",
                "color_theme": "blue"
            })
            day_counter += 1
            total_hotel_nights += 1

            for ev in day1_events:
                export_rows.append({
                    "date": travel_date.strftime("%d %b %Y"),
                    "leave_home_time": leave_home_str if ev["title"] == "Leave home" else "—",
                    "travel_to_airport": str(airport_drive_mins) if ev["title"] == "Leave home" else "—",
                    "time": ev["time"],
                    "activity": ev["activity_col"],
                    "location_details": ev["location_col"],
                    "transport": ev["transport"],
                    "distance": ev["distance"],
                    "duration": ev["duration"],
                    "booking_details": ev["booking_details"],
                    "map_link_text": ev["link_text"],
                    "map_link_url": ev["link"]
                })

        # ------------------------------------------------------------------
        # Inter-city Travel Day (between Meeting 1 and Meeting 2 if different)
        # ------------------------------------------------------------------
        elif idx > 0 and meet_city != prev_meeting.get("location", "").split(",")[0].strip():
            prev_meet_date = datetime.strptime(prev_meeting["date"], "%Y-%m-%d")
            inter_date = prev_meet_date + timedelta(days=1)
            inter_date_str = inter_date.strftime("%Y-%m-%d")
            display_inter_date = inter_date.strftime("%a, %d %b %Y")

            flight_info = get_flight_info(prev_dest_iata, dest_iata, 800.0)
            total_flights += 1

            day_inter_events = [
                {
                    "time": "07:30 AM",
                    "icon": "🚗",
                    "title": "Hotel to Airport",
                    "description": f"Car / Taxi (30 mins, 35 km)<br>📍 {prev_hotel} → {prev_dest_iata}",
                    "transport": "Taxi / Car",
                    "distance": "35 km",
                    "duration": "30 min",
                    "booking_details": "—",
                    "link_text": "View on Map",
                    "link": f"https://www.google.com/maps/search/?api=1&query={prev_hotel}+to+{prev_dest_iata}",
                    "activity_col": f"Hotel → {prev_dest_iata} Airport",
                    "location_col": f"{prev_hotel} → {prev_dest_iata}"
                },
                {
                    "time": "10:00 AM",
                    "icon": "✈️",
                    "title": f"Flight {flight_info['flight_code']}",
                    "description": f"{prev_dest_iata} → {dest_iata}<br>Duration: {flight_info['duration_str']}",
                    "transport": "Flight",
                    "distance": "—",
                    "duration": flight_info["duration_str"],
                    "booking_details": flight_info["flight_code"],
                    "link_text": "View Flight",
                    "link": f"https://www.google.com/travel/flights?q=flights+from+{prev_dest_iata}+to+{dest_iata}",
                    "activity_col": f"Flight: {prev_dest_iata} → {dest_iata}",
                    "location_col": f"{prev_dest_iata} → {dest_iata}"
                },
                {
                    "time": "01:50 PM",
                    "icon": "🚕",
                    "title": "Airport to Hotel",
                    "description": "Car / Taxi (25 mins, 25 km)",
                    "transport": "Taxi / Car",
                    "distance": "25 km",
                    "duration": "25 min",
                    "booking_details": "—",
                    "link_text": "View on Map",
                    "link": f"https://www.google.com/maps/search/?api=1&query={dest_iata}+to+{hotel_name}",
                    "activity_col": "Airport → Hotel",
                    "location_col": hotel_name
                },
                {
                    "time": "02:20 PM",
                    "icon": "🏨",
                    "title": f"Check-in — {hotel_name}",
                    "description": hotel_addr,
                    "transport": "Hotel",
                    "distance": "—",
                    "duration": "—",
                    "booking_details": f"Sleepover: {'Yes' if sleepover else 'No'}",
                    "link_text": "View Hotel",
                    "link": f"https://www.google.com/travel/hotels?q={hotel_name}+{meet_city}",
                    "activity_col": "Check-in & Rest",
                    "location_col": hotel_addr
                }
            ]

            days.append({
                "day_number": day_counter,
                "date": inter_date_str,
                "display_date": display_inter_date,
                "subtitle": f"Travel to {meet_city}",
                "events": day_inter_events,
                "overnight": f"Overnight stay: {hotel_name} ({inter_date.strftime('%d %b')})",
                "color_theme": "orange"
            })
            day_counter += 1
            total_hotel_nights += 1

            for ev in day_inter_events:
                export_rows.append({
                    "date": inter_date.strftime("%d %b %Y"),
                    "leave_home_time": "—",
                    "travel_to_airport": "—",
                    "time": ev["time"],
                    "activity": ev["activity_col"],
                    "location_details": ev["location_col"],
                    "transport": ev["transport"],
                    "distance": ev["distance"],
                    "duration": ev["duration"],
                    "booking_details": ev["booking_details"],
                    "map_link_text": ev["link_text"],
                    "map_link_url": ev["link"]
                })

        # ------------------------------------------------------------------
        # Meeting Day
        # ------------------------------------------------------------------
        display_meet_date = meeting_date.strftime("%a, %d %b %Y")
        hotel_to_meet_time = (datetime.combine(datetime.today(), meet_time) - timedelta(minutes=90)).strftime("%I:%M %p")
        arrive_meet_time = (datetime.combine(datetime.today(), meet_time) - timedelta(minutes=10)).strftime("%I:%M %p")

        meet_events = [
            {
                "time": hotel_to_meet_time,
                "icon": "🚗",
                "title": "Hotel to Meeting",
                "description": "Car / Taxi (20 mins, 12 km)",
                "transport": "Taxi / Car",
                "distance": "12 km",
                "duration": "20 min",
                "booking_details": "—",
                "link_text": "View on Map",
                "link": f"https://www.google.com/maps/search/?api=1&query={hotel_name}+to+{meet_loc}",
                "activity_col": f"Hotel → Meeting {idx + 1}",
                "location_col": meet_loc
            },
            {
                "time": arrive_meet_time,
                "icon": "🚶",
                "title": "Arrive at Meeting Location",
                "description": meet_loc,
                "transport": "Meeting",
                "distance": "—",
                "duration": "—",
                "booking_details": "—",
                "link_text": "View on Map",
                "link": f"https://www.google.com/maps/search/?api=1&query={meet_loc}",
                "activity_col": "Arrive at Meeting Location",
                "location_col": meet_loc
            },
            {
                "time": f"{meet_time_formatted} – {meet_end_formatted}",
                "icon": "🏢",
                "title": f"Meeting {idx + 1}",
                "description": f"{meet_loc}<br>Duration: 2 hrs",
                "transport": "Meeting",
                "distance": "—",
                "duration": "2 hrs",
                "booking_details": f"{meet_time_formatted} – {meet_end_formatted}",
                "link_text": "View on Map",
                "link": f"https://www.google.com/maps/search/?api=1&query={meet_loc}",
                "activity_col": f"Meeting {idx + 1}",
                "location_col": meet_loc
            },
            {
                "time": meet_end_formatted,
                "icon": "🚗",
                "title": "Return to Hotel" if (idx < len(sorted_meetings) - 1 or sleepover) else "Return to Airport",
                "description": "Car / Taxi (20 mins, 12 km)",
                "transport": "Taxi / Car",
                "distance": "12 km" if sleepover else "25 km",
                "duration": "20 min",
                "booking_details": "—",
                "link_text": "View on Map",
                "link": f"https://www.google.com/maps/search/?api=1&query={meet_loc}+to+{hotel_name}",
                "activity_col": f"Return to {'Hotel' if sleepover else 'Airport'}",
                "location_col": hotel_name if sleepover else f"{dest_iata} Airport"
            }
        ]

        if sleepover:
            meet_events.append({
                "time": "Rest of day",
                "icon": "🛏️",
                "title": "Free time / Rest",
                "description": hotel_name,
                "transport": "Hotel",
                "distance": "—",
                "duration": "—",
                "booking_details": "—",
                "link_text": "View Hotel",
                "link": f"https://www.google.com/travel/hotels?q={hotel_name}",
                "activity_col": "Free time / Rest",
                "location_col": hotel_name
            })
            total_hotel_nights += 1

        # If this is the last meeting and not sleeping over, add return flight
        is_last = (idx == len(sorted_meetings) - 1)
        if is_last:
            return_flight_info = get_flight_info(dest_iata, dept_iata, 1500.0)
            total_flights += 1

            meet_events.extend([
                {
                    "time": "02:30 PM",
                    "icon": "✈️",
                    "title": f"Flight {return_flight_info['flight_code']}",
                    "description": f"{dest_iata} → {dept_iata}<br>Duration: {return_flight_info['duration_str']}",
                    "transport": "Flight",
                    "distance": "—",
                    "duration": return_flight_info["duration_str"],
                    "booking_details": return_flight_info["flight_code"],
                    "link_text": "View Flight",
                    "link": f"https://www.google.com/travel/flights?q=flights+from+{dest_iata}+to+{dept_iata}",
                    "activity_col": f"Return Flight: {dest_iata} → {dept_iata}",
                    "location_col": f"{dest_iata} → {dept_iata}"
                },
                {
                    "time": "04:50 PM",
                    "icon": "🏁",
                    "title": f"Arrive at {origin_name} ({dept_iata})",
                    "description": "End of Trip<br>Arrived home safely",
                    "transport": "Home",
                    "distance": "—",
                    "duration": "—",
                    "booking_details": "—",
                    "link_text": "View on Map",
                    "link": f"https://www.google.com/maps/search/?api=1&query={origin_name}",
                    "activity_col": "Return to Initial Location",
                    "location_col": f"{meet_city} → {origin_name}"
                }
            ])

        days.append({
            "day_number": day_counter,
            "date": meet_date_str,
            "display_date": display_meet_date,
            "subtitle": f"Meeting {idx + 1} – {meet_loc}",
            "events": meet_events,
            "overnight": f"Overnight stay: {hotel_name} ({meeting_date.strftime('%d %b')})" if sleepover else "End of Trip",
            "color_theme": "green" if idx == 0 else "purple"
        })
        day_counter += 1

        for ev in meet_events:
            export_rows.append({
                "date": meeting_date.strftime("%d %b %Y"),
                "leave_home_time": "—",
                "travel_to_airport": "—",
                "time": ev["time"],
                "activity": ev["activity_col"],
                "location_details": ev["location_col"],
                "transport": ev["transport"],
                "distance": ev["distance"],
                "duration": ev["duration"],
                "booking_details": ev["booking_details"],
                "map_link_text": ev["link_text"],
                "map_link_url": ev["link"]
            })

        prev_meeting = meeting
        prev_hotel = hotel_name
        prev_dest_iata = dest_iata

    # Indicative cost calculation in SAR (matching UI mockup)
    flight_cost = total_flights * 2400
    hotel_cost = total_hotel_nights * 950
    transport_cost = len(days) * 200

    estimated_cost_sar = flight_cost + hotel_cost + transport_cost

    # Make all events compatible with planner.js
    for day in days:
        for event in day.get("events", []):
            normalize_event(event)

    return {
        "days": days,
        "export_rows": export_rows,
        "route_summary": route_summary,
        "total_flights": total_flights,
        "hotel_nights": total_hotel_nights,
        "total_cost_sar": f"SAR {estimated_cost_sar:,}"
    }
