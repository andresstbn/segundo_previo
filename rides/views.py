from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg

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

    # cambiar la disponibilidad
    @action(detail=True, methods=['post'], url_path='toggle-availability')
    def toggle_availability(self, request, pk=None):
        try:
            vehicle = self.get_object()
            vehicle.is_available = not vehicle.is_available
            vehicle.save()
            return Response({"is_available": vehicle.is_available})
        except Vehicle.DoesNotExist:
            return Response({"detail": "Vehicle not found."}, status=404)

    # resumen de vehículos modelo
    @action(detail=False, methods=['get'], url_path='models-summary')
    def models_summary(self, request):
        models_summary = Vehicle.objects.values('model').annotate(count=Count('id')).order_by('model')
        return Response(models_summary)


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

    # historial de viajes pasajero
    @action(detail=True, methods=['get'], url_path='trips')
    def passenger_trips(self, request, pk=None):
        trips = Trip.objects.filter(passenger_id=pk)
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

    # conteo de viajes (PENDING y ONGOING)
    @action(detail=False, methods=['get'], url_path='active-count')
    def active_count(self, request):
        pending_count = Trip.objects.filter(status=Trip.STATUS_PENDING).count()
        ongoing_count = Trip.objects.filter(status=Trip.STATUS_ONGOING).count()
        return Response({"pending": pending_count, "ongoing": ongoing_count})


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    #mejor promedio
    @action(detail=False, methods=['get'], url_path='trending')
    def trending(self, request):
        drivers = User.objects.filter(is_driver=True).annotate(
            average_score=Avg('trips_as_driver__rating__score')
        ).order_by('-average_score')

        top_drivers = drivers[:5]
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
