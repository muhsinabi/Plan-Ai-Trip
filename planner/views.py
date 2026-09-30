from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import (
    Trip,
    Participant,
    Meeting,
    ParticipantMeeting
)

from .airport_utils import find_nearest_airport
from .routing_utils import get_road_routing
from .itinerary_builder import build_complete_itinerary

import json
from datetime import datetime


@ensure_csrf_cookie
def planner_home(request):

    return render(
        request,
        "planner/dashboard.html"
    )


def generate_itinerary(request):

    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "POST request required"
        })

    try:

        data = json.loads(request.body)

        participants_data = data.get(
            "participants",
            []
        )

        trip = Trip.objects.create(
            name="Business Trip"
        )

        meeting_records = {}

        itinerary = []

        for participant_data in participants_data:

            # Create participant
            participant = Participant.objects.create(

                trip=trip,

                name=participant_data.get(
                    "name",
                    ""
                ),

                department=participant_data.get(
                    "department",
                    ""
                ),

                current_location=participant_data.get(
                    "current_location",
                    ""
                ),

                current_latitude=
                    participant_data.get(
                        "latitude"
                    ) or None,

                current_longitude=
                    participant_data.get(
                        "longitude"
                    ) or None
            )

            # Find nearest airport
            nearest_airport = find_nearest_airport(
                participant.current_latitude,
                participant.current_longitude
            )

            if nearest_airport:

                participant.departure_airport = (
                    f"{nearest_airport['name']} "
                    f"({nearest_airport['iata']})"
                )

                # Calculate real road distance and driving time using OSRM
                route = get_road_routing(
                    participant.current_latitude,
                    participant.current_longitude,
                    nearest_airport["latitude"],
                    nearest_airport["longitude"]
                )

                if route:
                    participant.airport_distance_km = route["distance_km"]
                    participant.airport_travel_minutes = route["duration_minutes"]
                else:
                    participant.airport_distance_km = nearest_airport["distance_km"]

                participant.save()

            # Create participant itinerary
            participant_itinerary = {

                "name":
                    participant.name,

                "department":
                    participant.department,

                "current_location":
                    participant.current_location,

                "departure_airport":
                    participant.departure_airport,

                "airport_distance_km":
                    float(
                        participant.airport_distance_km
                    )
                    if participant.airport_distance_km
                    else None,

                "airport_travel_minutes":
                    participant.airport_travel_minutes,

                "meetings": [],

                "days": []
            }

            # Process meetings
            for meeting_data in participant_data.get(
                "meetings",
                []
            ):

                location = meeting_data.get(
                    "location",
                    ""
                )

                date = meeting_data.get(
                    "date"
                )

                time = meeting_data.get(
                    "time"
                )

                if not location or not date or not time:
                    continue

                # Convert meeting time
                try:

                    meeting_time = datetime.strptime(
                        time,
                        "%I:%M %p"
                    ).time()

                except ValueError:

                    meeting_time = datetime.strptime(
                        time,
                        "%H:%M"
                    ).time()

                meeting_key = (
                    location.strip().lower(),
                    date,
                    meeting_time
                )

                # Check if meeting already exists
                if meeting_key in meeting_records:

                    meeting = meeting_records[
                        meeting_key
                    ]

                else:

                    meeting = Meeting.objects.create(

                        trip=trip,

                        title="Business Meeting",

                        location=location,

                        latitude=
                            meeting_data.get(
                                "latitude"
                            ) or None,

                        longitude=
                            meeting_data.get(
                                "longitude"
                            ) or None,

                        meeting_date=date,

                        meeting_time=meeting_time,

                        duration_minutes=120
                    )

                    meeting_records[
                        meeting_key
                    ] = meeting

                # Sleepover
                sleepover = (
                    meeting_data.get(
                        "sleepover"
                    ) == "yes"
                )

                hotel_name = meeting_data.get("hotel_name", "")

                ParticipantMeeting.objects.create(
                    participant=participant,
                    meeting=meeting,
                    hotel_name=hotel_name,
                    sleepover=sleepover
                )

                # Add meeting to itinerary
                participant_itinerary[
                    "meetings"
                ].append({
                    "number":
                        meeting_data.get("number"),
                    "location":
                        location,
                    "date":
                        date,
                    "time":
                        time,
                    "hotel_name":
                        hotel_name,
                    "sleepover":
                        sleepover
                })

            # Build rich complete day-by-day business itinerary
            travel_plan = build_complete_itinerary(
                participant,
                participant_data.get("meetings", [])
            )

            participant_itinerary["days"] = travel_plan["days"]
            participant_itinerary["export_rows"] = travel_plan["export_rows"]
            participant_itinerary["route_summary"] = travel_plan["route_summary"]
            participant_itinerary["total_flights"] = travel_plan["total_flights"]
            participant_itinerary["hotel_nights"] = travel_plan["hotel_nights"]
            participant_itinerary["total_cost_sar"] = travel_plan["total_cost_sar"]

            itinerary.append(participant_itinerary)

        return JsonResponse({

            "success":
                True,

            "message":
                "Trip saved successfully",

            "trip_id":
                trip.id,

            "participants":
                len(participants_data),

            "meetings":
                len(meeting_records),

            "itinerary":
                itinerary
        })

    except Exception as e:

        return JsonResponse({

            "success":
                False,

            "message":
                str(e)
        })