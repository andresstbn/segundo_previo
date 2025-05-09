from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    VehicleViewSet,
    TripViewSet,
    DriverViewSet,
    RatingViewSet,
    HomeView,
    passengerViewSet
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'trips', TripViewSet, basename='trip')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'passenger', passengerViewSet, basename='passenger')

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('api/', include(router.urls)),
]
