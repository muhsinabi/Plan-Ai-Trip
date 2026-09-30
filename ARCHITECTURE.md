# AI Business Travel Itinerary Planner

## Phase 1: project and data design

The project uses a small Django application with the `config` package for
settings and URL routing, and the `planner` app for trip planning logic and
data. Browser assets live in `static/css` and `static/js`; page templates live
in `planner/templates/planner`. PostgreSQL is the configured database, with
connection details supplied through environment variables.

### Data model

- **Trip** is the planning workspace and owns participants and meetings.
- **Participant** stores a traveler's department, origin and optional
  geocoded location details, plus nearest-airport data when it is calculated.
- **Meeting** stores a trip stop, its schedule, and optional geocoded location
  details.
- **ParticipantMeeting** joins participants to meetings and holds participant-
  specific hotel and overnight choices.
- **TravelLeg** stores ordered ground-transport segments and their route data.
- **Flight** stores confirmed flight details only; unavailable flight data is
  represented by the absence of a flight record rather than fabricated values.

The existing `planner` modules keep airport lookup, road routing, and itinerary
assembly separate from database models. Later phases can add provider-backed
location search, routing, hotels, and flights without putting API code into the
models.

### Local database configuration

Copy `.env.example` values into the environment used to run Django and provide
your own PostgreSQL credentials. The application does not store database
passwords in source control.
