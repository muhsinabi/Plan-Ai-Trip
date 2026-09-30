from django.urls import path
from .views import planner_home, generate_itinerary


urlpatterns = [
    path("", planner_home, name="planner_home"),
    path("generate-itinerary/", generate_itinerary, name="generate_itinerary"),
]