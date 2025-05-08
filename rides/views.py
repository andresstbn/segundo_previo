from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from rest_framework import status

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

    @action(detail=False, methods=['post'], url_path='request')
    def request_trip(self, request):
        user = request.user

        if not user.is_authenticated or not user.is_passenger:
            return Response({'detail': 'Solo los pasajeros autenticados pueden solicitar viajes.'},
                            status=status.HTTP_403_FORBIDDEN)

        # Filtro para conductores disponibles
        drivers = User.objects.filter(is_driver=True, is_available=True) \
            .annotate(active_trips=Count('trips_as_driver', filter=Q(trips_as_driver__status__in=['PENDING', 'ONGOING']))) \
            .order_by('active_trips')

        if not drivers.exists():
            return Response({'detail': 'No hay conductores disponibles.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Crear el viaje
        trip = Trip.objects.create(
            passenger=user,
            driver=selected_driver,
            status=Trip.STATUS_PENDING
        )

        serializer = self.get_serializer(trip)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='status')
    def get_status(self, request, pk=None):
        try:
            trip = self.get_object()
        except Trip.DoesNotExist:
            return Response({'detail': 'Viaje no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': trip.status})

        selected_driver = drivers.first()

class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='ratings')
    def ratings(self, request, pk=None):
        try:
            driver = self.get_object()
        except User.DoesNotExist:
            return Response({'detail': 'Conductor no encontrado.'}, status=404)

        ratings = Rating.objects.filter(trip__driver=driver)
        serializer = RatingSerializer(ratings, many=True)
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
