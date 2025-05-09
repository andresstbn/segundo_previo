from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg


from .models import Rating, Trip, Vehicle, CustomUser
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
    permission_classes = []

    @action(detail=True, methods=['post'], url_path='toggle-availability')
    def toggle_availability(self, request, pk=None):
        """
        Endpoint para alternar la disponibilidad de un vehículo.
        """
        try:
            vehicle = self.get_object()
            vehicle.is_available = not vehicle.is_available
            vehicle.save()
            return Response({"is_available": vehicle.is_available}, status=status.HTTP_200_OK)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='models-summary')
    def models_summary(self, request):
        """
        Endpoint para obtener un resumen de modelos de vehículos y sus cantidades.
        """
        summary = Vehicle.objects.values('model').annotate(count=Count('model'))
        return Response(summary, status=status.HTTP_200_OK)

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

    @action(detail=False, methods=['get'], url_path='active-count')
    def active_count(self, request):
        """
        Endpoint para obtener el número de viajes en estado PENDING y ONGOING.
        """
        pending_count = Trip.objects.filter(status='PENDING').count()
        ongoing_count = Trip.objects.filter(status='ONGOING').count()
        return Response({"pending": pending_count, "ongoing": ongoing_count}, status=status.HTTP_200_OK)

class PassengerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar pasajeros y sus viajes.
    """
    queryset = CustomUser.objects.filter(is_passenger=True)  # Filtra solo pasajeros
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='trips')
    def trips(self, request, pk=None):
        """
        Endpoint para listar todos los viajes de un pasajero.
        """
        try:
            passenger = self.get_object()  # Obtiene el pasajero con el ID proporcionado
            trips = Trip.objects.filter(passenger=passenger)  # Filtra los viajes por pasajero
            serializer = TripSerializer(trips, many=True)  # Serializa los viajes
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "Passenger not found"}, status=status.HTTP_404_NOT_FOUND)

class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='trending')
    def trending(self, request):
        """
        Endpoint para obtener los 5 conductores con mejor puntaje promedio.
        """
        trending_drivers = (
            User.objects.filter(is_driver=True)
            .annotate(average_score=Avg('trips_as_driver__rating__score'))
            .order_by('-average_score')[:5]
        )
        data = [
            {
                "id": driver.id,
                "name": driver.get_full_name(),
                "average_score": driver.average_score,
            }
            for driver in trending_drivers
        ]
        return Response(data, status=status.HTTP_200_OK)


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
