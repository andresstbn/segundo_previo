from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Trip, CustomUser
from .serializers import TripSerializer


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

    # POST /api/trips/request/
    @action(detail=False, methods=['post'])
    def request(self, request):
        # Filtra conductores disponibles
        available_drivers = User.objects.filter(
            is_driver=True,
            is_available=True
        ).annotate(
            active_trips=Count('driver_trips', filter=Q(driver_trips__status__in=['PENDING', 'ONGOING']))
        ).order_by('active_trips')

        if not available_drivers.exists():
            return Response(
                {"error": "No hay conductores disponibles"},
                status=status.HTTP_400_BAD_REQUEST
            )

        selected_driver = available_drivers.first()

        # Crea el viaje
        trip = Trip.objects.create(
            passenger=request.user,
            driver=selected_driver,
            status='PENDING'
        )

        serializer = TripSerializer(trip)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        trip = self.get_object()
        return Response({"status": trip.status})

    def get_queryset(self):
        queryset = super().get_queryset()
        driver_id = self.request.query_params.get('driver')
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        return queryset


class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        ratings = Rating.objects.filter(trip__driver_id=pk)
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
