from django.db import models


class Trip(models.Model):
    name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Trip {self.id}"


class Participant(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    name = models.CharField(max_length=200)
    department = models.CharField(max_length=200, blank=True)

    # Starting point of the participant
    current_location = models.CharField(max_length=500)
    current_region = models.CharField(max_length=200, blank=True)
    current_country = models.CharField(max_length=200, blank=True)
    current_timezone = models.CharField(max_length=64, blank=True)
    current_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )
    current_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )

    # Airport information calculated later
    departure_airport = models.CharField(
        max_length=300, blank=True
    )
    departure_airport_iata = models.CharField(max_length=3, blank=True)
    departure_airport_icao = models.CharField(max_length=4, blank=True)
    departure_airport_latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    departure_airport_longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    airport_distance_km = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    airport_travel_minutes = models.PositiveIntegerField(
        null=True, blank=True
    )

    def __str__(self):
        return self.name


class Meeting(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="meetings"
    )

    title = models.CharField(max_length=300, blank=True)

    location = models.CharField(max_length=500)
    region = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    timezone = models.CharField(max_length=64, blank=True)

    latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )

    meeting_date = models.DateField()
    meeting_time = models.TimeField()

    duration_minutes = models.PositiveIntegerField(
        default=120
    )

    def __str__(self):
        return f"{self.location} - {self.meeting_date}"


class ParticipantMeeting(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="meeting_plans"
    )

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="participants"
    )

    # Hotel selected for this participant around this meeting
    hotel_name = models.CharField(
        max_length=300,
        blank=True
    )

    hotel_address = models.CharField(
        max_length=500,
        blank=True
    )

    hotel_latitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )

    hotel_longitude = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True
    )

    # Whether participant stays overnight
    sleepover = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant", "meeting"],
                name="unique_participant_meeting"
            )
        ]

    def __str__(self):
        return f"{self.participant.name} - {self.meeting.location}"


class TravelLeg(models.Model):
    """
    Stores each movement in the itinerary.

    Examples:
    Home → Airport
    Airport → Hotel
    Hotel → Meeting
    Meeting → Hotel
    Hotel → Airport
    Airport → Home
    """

    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="travel_legs"
    )

    from_location = models.CharField(max_length=500)
    to_location = models.CharField(max_length=500)

    distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    travel_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    transport_mode = models.CharField(
        max_length=100,
        blank=True
    )

    departure_datetime = models.DateTimeField(
        null=True,
        blank=True
    )

    arrival_datetime = models.DateTimeField(
        null=True,
        blank=True
    )

    maps_url = models.URLField(
        blank=True
    )

    sequence = models.PositiveIntegerField(
        default=1
    )

    def __str__(self):
        return f"{self.from_location} → {self.to_location}"


class Flight(models.Model):
    """
    Flight information selected by the itinerary planner.
    """

    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="flights"
    )

    flight_number = models.CharField(
        max_length=100,
        blank=True
    )

    airline = models.CharField(
        max_length=200,
        blank=True
    )

    departure_airport = models.CharField(
        max_length=100
    )

    arrival_airport = models.CharField(
        max_length=100
    )

    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()

    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.flight_number}: "
            f"{self.departure_airport} → "
            f"{self.arrival_airport}"
        )
