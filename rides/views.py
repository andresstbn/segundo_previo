from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.db.models import Avg
from rest_framework.decorators import action

from .models import Rating, Trip, Vehicle
from .serializers import (
    RatingSerializer,
    TripSerializer,
    UserSerializer,
    VehicleSerializer,
)

User = get_user_model()


class HomeView(TemplateView):
    """
    Vista de inicio de la aplicación.
    """
    template_name = 'rides/home.html'


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de vehículos.
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        vehicle = self.get_object()
        vehicle.driver.is_available = not vehicle.driver.is_available
        vehicle.driver.save()
        return Response({'is_available': vehicle.driver.is_available})

    @action(detail=False, methods=['get'])
    def models_summary(self, request):
        summary = Vehicle.objects.values('model').annotate(count=Count('id')).order_by('-count')
        return Response(summary)


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar trips.

    Soporta filtro por driver con ?driver=<id>.
    """
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['driver']

    @action(detail=False, methods=['get'])
    def active_count(self, request):
        pending = Trip.objects.filter(status=Trip.STATUS_PENDING).count()
        ongoing = Trip.objects.filter(status=Trip.STATUS_ONGOING).count()
        return Response({'pending': pending, 'ongoing': ongoing})


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def frending(self, request):
        top_drivers = User.objects.filter(
            is_driver=True,
            trips_as_driver__rating__isnull=False
        ).annotate(
            average_score=Avg('trips_as_driver__rating__score')
        ).order_by('-average_score')[:5]
        
        serializer = UserSerializer(top_drivers, many=True)
        return Response(serializer.data)


class RatingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para listar, detallar y actualizar ratings, pero no borrar.
    """
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]


class PassengerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_passenger=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def trips(self, request, pk=None):
        passenger = self.get_object()
        trips = Trip.objects.filter(passenger=passenger)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)