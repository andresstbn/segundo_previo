from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets

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

    # Metodo para filtrar Usuarios con is_driver=True e is_available=True
    def get_queryset(self):
        queryset = super().get_queryset()
        driver_id = self.request.query_params.get('driver')
        if driver_id:
            queryset = queryset.filter(driver__id=driver_id, driver__is_available=True)
        return queryset
    
class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver conductores.
    """
    queryset = User.objects.filter(is_driver=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


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
