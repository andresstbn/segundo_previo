from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Rating, Trip, Vehicle
from .serializers import TripSerializer, UserSerializer, VehicleSerializer, RatingSerializer

User = get_user_model()

class HomeView(TemplateView):
    template_name = 'rides/home.html'

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['driver']

    @action(detail=False, methods=['post'], url_path='request')
    def request_trip(self, request):
        if not request.user.is_passenger:
            return Response({"detail": "Only passengers can request trips."}, status=403)

        drivers = User.objects.filter(
            is_driver=True,
            is_available=True
        ).annotate(
            active_trips=Count(
                'trips_as_driver',
                filter=Q(trips_as_driver__status__in=[Trip.STATUS_PENDING, Trip.STATUS_ONGOING])
            )
        )

        selected_driver = drivers.order_by('active_trips').first()
        if not selected_driver:
            return Response({"detail": "No drivers available."}, status=400)

        trip = Trip.objects.create(
            passenger=request.user,
            driver=selected_driver,
            status=Trip.STATUS_PENDING
        )

        serializer = self.get_serializer(trip)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['get'], url_path='status')
    def status(self, request, pk=None):
        trip = self.get_object()
        return Response({'status': trip.status})

class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_driver=True).annotate(
        trip_count=Count(
            'trips_as_driver',
            filter=Q(trips_as_driver__status=Trip.STATUS_COMPLETED)
        )
    )
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='ratings')
    def ratings(self, request, pk=None):
        driver = self.get_object()
        ratings = Rating.objects.filter(trip__driver=driver)
        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = RatingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data)

class RatingViewSet(viewsets.GenericViewSet,
                    viewsets.mixins.ListModelMixin,
                    viewsets.mixins.RetrieveModelMixin,
                    viewsets.mixins.UpdateModelMixin):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
